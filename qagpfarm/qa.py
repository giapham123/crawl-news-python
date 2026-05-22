import argparse
import json
import os
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Sequence

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional convenience dependency
    load_dotenv = None

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - handled at runtime with offline fallback
    OpenAI = None


CONTEXT_PATH = Path(__file__).with_name("context.md")
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
DEFAULT_BASE_URL = "http://localhost:20128/v1"
DEFAULT_MODEL = "cx/gpt-5.3-codex-none"

INTENTS = {"product_info", "price_stock", "recommendation", "brand_contact"}
GREETING_RESPONSE = "Dạ GP Farm chào bạn. Bạn cần mình tư vấn sản phẩm, báo giá hay gợi ý món phù hợp ạ?"

ORCHESTRATOR_PROMPT = """
Bạn là Orchestrator của hệ thống tư vấn GP Farm.
Phân loại câu hỏi của khách hàng vào một trong bốn nhóm: product_info, price_stock, recommendation, brand_contact.
Trả lời JSON: {"intent": "<category>", "query": "<original query>"}.
Không giải thích thêm.
""".strip()

PRODUCT_INFO_SYSTEM_PROMPT = """
Bạn là chuyên viên tư vấn sản phẩm của GP Farm. Dựa vào dữ liệu sản phẩm được cung cấp, hãy trả lời chi tiết,
chính xác và thân thiện về mô tả, thành phần, điểm bán hàng, cách dùng và lưu ý dị ứng của sản phẩm.
Nếu không có thông tin trong dữ liệu, hãy nói: "Hiện tại mình chưa có thông tin chi tiết về vấn đề này,
bạn vui lòng liên hệ GP Farm qua Zalo 0949246147 để được hỗ trợ nhé!"
""".strip()

PRICE_STOCK_SYSTEM_PROMPT = """
Bạn là nhân viên tư vấn giá và tồn kho của GP Farm. Trả lời chính xác giá theo từng size, tình trạng hàng,
và so sánh giá nếu khách yêu cầu. Luôn hiển thị đầy đủ các lựa chọn size. Nếu sản phẩm hết hàng,
thông báo rõ và gợi ý sản phẩm thay thế nếu phù hợp.
""".strip()

RECOMMENDATION_SYSTEM_PROMPT = """
Bạn là chuyên gia tư vấn dinh dưỡng và lựa chọn sản phẩm của GP Farm. Dựa trên nhu cầu, mục tiêu sức khỏe
hoặc dịp dùng của khách, hãy gợi ý 2-3 sản phẩm phù hợp nhất kèm lý do ngắn gọn và giá tham khảo.
Ưu tiên sản phẩm còn hàng.
""".strip()

BRAND_CONTACT_SYSTEM_PROMPT = """
Bạn là đại diện thương hiệu GP Farm. Cung cấp thông tin liên hệ, mạng xã hội, và hướng dẫn khách đặt hàng
trực tiếp trên website https://gpfarm.net, qua Zalo 0949246147 hoặc nhắn tin Facebook page GP Farm.
Nếu khách muốn đặt hàng qua chat, hãy xin tên sản phẩm, size/số lượng, tên người nhận, số điện thoại
và địa chỉ giao hàng. Luôn thân thiện và nhiệt tình.
""".strip()

CONVERSATION_STYLE_PROMPT = """
Phong cách trả lời:
- Trả lời như một nhân viên tư vấn GP Farm đang chat trực tiếp với khách.
- Tự nhiên, gần gũi, rõ ý; ưu tiên tiếng Việt nếu khách dùng tiếng Việt.
- Viết như người thật đang nhắn tin: mở đầu nhẹ nhàng, không quá máy móc, không dùng văn phong báo cáo.
- Tránh trả lời chỉ bằng danh sách khô cứng. Có thể dùng bullet để giá dễ đọc, nhưng nên có câu dẫn và câu chốt thân thiện.
- Không dùng markdown bold hoặc ký tự ** trong câu trả lời gửi khách.
- Không bịa thông tin ngoài knowledge base. Nếu thiếu dữ liệu, hướng khách liên hệ Zalo 0949246147.
- Nếu khách hỏi giá/tồn kho, luôn nêu đầy đủ size và tình trạng hàng.
- Nếu khách đang nối tiếp câu trước, dùng lịch sử hội thoại để hiểu ngữ cảnh.
""".strip()

AGENT_PROMPTS = {
    "product_info": PRODUCT_INFO_SYSTEM_PROMPT,
    "price_stock": PRICE_STOCK_SYSTEM_PROMPT,
    "recommendation": RECOMMENDATION_SYSTEM_PROMPT,
    "brand_contact": BRAND_CONTACT_SYSTEM_PROMPT,
}


@dataclass(frozen=True)
class IntentResult:
    intent: str
    query: str


@dataclass(frozen=True)
class Product:
    id: int
    name: str
    category: str
    price: str
    stock: str
    detail: str = ""


def _load_context(path: Path = CONTEXT_PATH) -> str:
    return path.read_text(encoding="utf-8")


def _normalize(value: str) -> str:
    value = value.replace("đ", "d").replace("Đ", "D")
    decomposed = unicodedata.normalize("NFD", value.lower())
    without_marks = "".join(char for char in decomposed if unicodedata.category(char) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", without_marks).strip()


def _strip_markdown(value: str) -> str:
    return re.sub(r"[*_`]+", "", value).strip()


def _clean_customer_reply(value: str) -> str:
    return value.replace("*", "").replace("__", "")


def _is_greeting(query: str) -> bool:
    normalized = _normalize(query)
    return normalized in {
        "hi",
        "hello",
        "hey",
        "chao",
        "xin chao",
        "chao ban",
        "alo",
        "helo",
    }


def _parse_products(context: str) -> Dict[int, Product]:
    products: Dict[int, Product] = {}
    in_table = False

    for line in context.splitlines():
        if line.startswith("| ID | Tên sản phẩm |"):
            in_table = True
            continue
        if in_table and not line.startswith("|"):
            break
        if not in_table or line.startswith("|----"):
            continue

        cells = [_strip_markdown(cell) for cell in line.strip("|").split("|")]
        if len(cells) != 5 or not cells[0].strip().isdigit():
            continue
        product_id = int(cells[0].strip())
        products[product_id] = Product(
            id=product_id,
            name=cells[1].strip(),
            category=cells[2].strip(),
            price=cells[3].strip(),
            stock=cells[4].strip(),
        )

    detail_pattern = re.compile(
        r"#### ID (?P<id>\d+) — (?P<name>[^\n]+)\n(?P<body>.*?)(?=\n#### ID \d+ —|\n---\n\n## Model Configuration|\Z)",
        re.DOTALL,
    )
    for match in detail_pattern.finditer(context):
        product_id = int(match.group("id"))
        existing = products.get(product_id)
        clean_name = _strip_markdown(re.sub(r"\s*\([^)]*\)\s*$", "", match.group("name")).strip())
        detail = match.group("body").strip()
        if existing:
            products[product_id] = Product(
                id=existing.id,
                name=existing.name,
                category=existing.category,
                price=existing.price,
                stock=existing.stock,
                detail=detail,
            )
        else:
            products[product_id] = Product(
                id=product_id,
                name=clean_name,
                category="",
                price="",
                stock="",
                detail=detail,
            )

    return products


class GPFarmQA:
    def __init__(
        self,
        context_path: Path = CONTEXT_PATH,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        use_llm: bool = True,
    ) -> None:
        if load_dotenv:
            load_dotenv(ENV_PATH)

        self.context_path = context_path
        self.context = _load_context(context_path)
        self.products = _parse_products(self.context)
        self.model = model or os.getenv("OPENAI_MODEL", DEFAULT_MODEL)
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", DEFAULT_BASE_URL)
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.use_llm = use_llm
        self.client = self._build_client()

    def _build_client(self):
        if not self.use_llm or OpenAI is None:
            return None
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required. Add it to .env or export it before starting the app.")
        return OpenAI(api_key=self.api_key, base_url=self.base_url)

    def classify(self, query: str) -> IntentResult:
        if self.client:
            try:
                content = self._call_agent(ORCHESTRATOR_PROMPT, query, inject_context=False)
                parsed = json.loads(content)
                intent = parsed.get("intent")
                if intent in INTENTS:
                    return IntentResult(intent=intent, query=parsed.get("query") or query)
            except Exception:
                pass

        return IntentResult(intent=self._classify_offline(query), query=query)

    def answer(self, query: str) -> str:
        if _is_greeting(query):
            return GREETING_RESPONSE

        routed = self.classify(query)
        return self.answer_with_intent(routed.intent, routed.query)

    def answer_with_graph(self, query: str, history: Optional[Sequence[Dict[str, str]]] = None) -> str:
        if _is_greeting(query):
            return GREETING_RESPONSE

        from qagpfarm.graph.builder import build_graph

        app = build_graph(self)
        result = app.invoke(
            {
                "query": query,
                "routed_query": query,
                "intent": "",
                "answer": "",
                "history": list(history or []),
                "error": None,
            }
        )
        return result.get("answer") or "Mình chưa tạo được câu trả lời. Bạn vui lòng thử lại nhé!"

    def answer_with_intent(
        self,
        intent: str,
        query: str,
        history: Optional[Sequence[Dict[str, str]]] = None,
    ) -> str:
        system_prompt = AGENT_PROMPTS.get(intent, PRODUCT_INFO_SYSTEM_PROMPT)
        full_prompt = f"{system_prompt}\n\n{CONVERSATION_STYLE_PROMPT}\n\n[KNOWLEDGE BASE]\n{self.context}"

        if self.client:
            try:
                return _clean_customer_reply(self._call_agent(full_prompt, query, inject_context=False, history=history))
            except Exception as exc:
                fallback = self._answer_offline(intent, query)
                return _clean_customer_reply(f"{fallback}\n\n(Lưu ý: đang dùng trả lời offline vì chưa gọi được model: {exc})")

        return _clean_customer_reply(self._answer_offline(intent, query))

    def stream_answer_with_intent(
        self,
        intent: str,
        query: str,
        history: Optional[Sequence[Dict[str, str]]] = None,
    ) -> Iterator[str]:
        system_prompt = AGENT_PROMPTS.get(intent, PRODUCT_INFO_SYSTEM_PROMPT)
        full_prompt = f"{system_prompt}\n\n{CONVERSATION_STYLE_PROMPT}\n\n[KNOWLEDGE BASE]\n{self.context}"

        if self.client:
            try:
                for chunk in self._stream_call_agent(full_prompt, query, inject_context=False, history=history):
                    yield _clean_customer_reply(chunk)
                return
            except Exception as exc:
                fallback = self._answer_offline(intent, query)
                yield _clean_customer_reply(f"{fallback}\n\n(Lưu ý: đang dùng trả lời offline vì chưa stream được model: {exc})")
                return

        yield _clean_customer_reply(self._answer_offline(intent, query))

    def _build_messages(
        self,
        system_prompt: str,
        user_query: str,
        inject_context: bool = True,
        history: Optional[Sequence[Dict[str, str]]] = None,
    ) -> List[Dict[str, str]]:
        prompt = f"{system_prompt}\n\n[KNOWLEDGE BASE]\n{self.context}" if inject_context else system_prompt
        messages = [{"role": "system", "content": prompt}]
        for message in list(history or [])[-12:]:
            role = message.get("role")
            content = message.get("content")
            if role in {"user", "assistant"} and content:
                messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": user_query})
        return messages

    def _call_agent(
        self,
        system_prompt: str,
        user_query: str,
        inject_context: bool = True,
        history: Optional[Sequence[Dict[str, str]]] = None,
    ) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self._build_messages(system_prompt, user_query, inject_context, history),
        )
        return response.choices[0].message.content or ""

    def _stream_call_agent(
        self,
        system_prompt: str,
        user_query: str,
        inject_context: bool = True,
        history: Optional[Sequence[Dict[str, str]]] = None,
    ) -> Iterator[str]:
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=self._build_messages(system_prompt, user_query, inject_context, history),
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta
            content = getattr(delta, "content", None)
            if content:
                yield content

    def _classify_offline(self, query: str) -> str:
        normalized = _normalize(query)
        if any(word in normalized for word in ["gia", "bao nhieu", "con hang", "het hang", "ton kho", "size"]):
            return "price_stock"
        if any(word in normalized for word in ["goi y", "tu van", "nen mua", "phu hop", "qua tang", "an kieng", "keto", "bau", "tre em"]):
            return "recommendation"
        if any(word in normalized for word in ["lien he", "zalo", "facebook", "tiktok", "website", "dat hang", "mua o dau", "email"]):
            return "brand_contact"
        return "product_info"

    def _answer_offline(self, intent: str, query: str) -> str:
        if intent == "price_stock":
            return self._price_stock_answer(query)
        if intent == "recommendation":
            return self._recommendation_answer(query)
        if intent == "brand_contact":
            return self._brand_contact_answer()
        return self._product_info_answer(query)

    def _find_products(self, query: str) -> List[Product]:
        normalized_query = _normalize(query)
        query_tokens = set(normalized_query.split())
        matches: List[Product] = []

        for product in self.products.values():
            haystack = _normalize(f"{product.name} {product.category}")
            if normalized_query and normalized_query in haystack:
                matches.append(product)
                continue

            name_tokens = set(_normalize(product.name).split())
            meaningful_overlap = query_tokens & name_tokens - {"hat", "nhan", "say", "tu", "nhien", "mix"}
            if meaningful_overlap and len(meaningful_overlap) >= min(2, len(query_tokens)):
                matches.append(product)

        if matches:
            return matches

        category_aliases = {
            "granola": "Granola",
            "cafe": "Cafe",
            "ca phe": "Cafe",
            "mat ong": "Mật ong & nghệ",
            "nghe": "Mật ong & nghệ",
            "banh": "Bánh mix hạt",
            "trai cay": "Trái cây sấy",
            "xoai": "Trái cây sấy",
            "hat": "Các loại hạt",
            "macca": "Các loại hạt",
            "oc cho": "Các loại hạt",
            "dieu": "Các loại hạt",
        }
        for alias, category in category_aliases.items():
            if alias in normalized_query:
                return [product for product in self.products.values() if product.category == category]
        return []

    def _price_stock_answer(self, query: str) -> str:
        products = self._find_products(query)
        if not products:
            return "Dạ bạn cho mình xin tên sản phẩm cụ thể hơn một chút nhé, mình sẽ báo đúng giá và tình trạng hàng cho bạn. Nếu cần nhanh, bạn cũng có thể nhắn Zalo 0949246147 ạ."

        lines = ["Dạ GP Farm gửi bạn giá và tình trạng hàng hiện tại nhé:"]
        for product in products[:8]:
            lines.append(f"- {product.name}: {product.price}. Tình trạng: {product.stock}.")
        if len(products) > 8:
            lines.append("Bạn nhắn thêm tên món cụ thể giúp mình, mình lọc lại cho gọn và dễ chọn hơn ạ.")
        else:
            lines.append("Bạn muốn lấy size nào thì nhắn mình, GP Farm hỗ trợ lên đơn qua website, Zalo hoặc Facebook nhé.")
        return "\n".join(lines)

    def _product_info_answer(self, query: str) -> str:
        products = self._find_products(query)
        if not products:
            return "Dạ phần này hiện mình chưa có đủ thông tin chi tiết trong dữ liệu sản phẩm. Bạn nhắn GP Farm qua Zalo 0949246147 để bên mình kiểm tra và tư vấn kỹ hơn nhé."

        product = products[0]
        detail_lines = [line for line in product.detail.splitlines() if line.startswith("- **")]
        if not detail_lines:
            return f"Dạ {product.name} hiện {product.stock.lower()}, giá {product.price}. Bạn muốn mình tư vấn thêm cách dùng hoặc size phù hợp thì nhắn mình nhé."

        lines = [f"Dạ món {product.name} bên mình có thông tin như sau:"]
        for line in detail_lines:
            lines.append(f"- {_strip_markdown(line[2:])}")
        if product.price:
            lines.append(f"- Giá: {product.price}. Tình trạng: {product.stock}.")
        lines.append("Bạn cần mình gợi ý size hoặc cách đặt hàng thì mình hỗ trợ tiếp ạ.")
        return "\n".join(lines)

    def _recommendation_answer(self, query: str) -> str:
        normalized = _normalize(query)
        picks: List[int]
        reason: str

        if any(word in normalized for word in ["keto", "low carb", "an kieng", "giam can"]):
            picks = [16, 22, 24]
            reason = "phù hợp ăn healthy, ít tinh bột hơn và ưu tiên sản phẩm còn hàng"
        elif any(word in normalized for word in ["qua", "bieu", "tang", "cao cap"]):
            picks = [1, 6, 21]
            reason = "hình thức đẹp, vị dễ dùng và hợp làm quà"
        elif any(word in normalized for word in ["bau", "me bau", "tre em", "be"]):
            picks = [8, 9, 17]
            reason = "nhóm sản phẩm dễ tư vấn cho gia đình, bà bầu hoặc trẻ em lớn"
        elif any(word in normalized for word in ["cafe", "ca phe", "robusta", "arabica"]):
            picks = [25, 29, 26]
            reason = "đủ lựa chọn từ gu cân bằng, thơm thanh đến đậm kiểu Việt"
        elif any(word in normalized for word in ["tieu hoa", "suc khoe", "nghe", "da day"]):
            picks = [19, 20, 18]
            reason = "phù hợp nhu cầu hỗ trợ sức khỏe hằng ngày"
        else:
            picks = [15, 11, 12]
            reason = "dễ ăn hằng ngày, hợp làm snack healthy"

        lines = [f"Dạ với nhu cầu này, mình gợi ý vài món khá hợp vì {reason}:"]
        for product_id in picks:
            product = self.products[product_id]
            lines.append(f"- {product.name}: {product.price}, {product.stock}.")
        lines.append("Bạn thích vị dễ ăn hay muốn chọn món cao cấp hơn để mình lọc tiếp cho sát nhé.")
        return "\n".join(lines)

    def _brand_contact_answer(self) -> str:
        return "\n".join(
            [
                "Dạ bạn có thể đặt hàng trực tiếp với GP Farm qua một trong các kênh này nhé:",
                "- Website: https://gpfarm.net",
                "- Zalo: 0949246147",
                "- Facebook message: https://www.facebook.com/gp.farm47/",
                "",
                "Nếu đặt qua chat, bạn gửi giúp mình: tên sản phẩm, size/số lượng, tên người nhận, số điện thoại và địa chỉ giao hàng là bên mình hỗ trợ lên đơn ạ.",
                "",
                "Thông tin liên hệ khác:",
                "- Email: gpfarm47@gmail.com",
                "- TikTok: https://www.tiktok.com/@gpfarm47",
            ]
        )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GP Farm multi-agent Q&A assistant")
    parser.add_argument("query", nargs="*", help="Câu hỏi của khách hàng")
    parser.add_argument("--offline", action="store_true", help="Không gọi OpenAI/local proxy, chỉ dùng fallback nội bộ")
    parser.add_argument("--langgraph", action="store_true", help="Chạy flow bằng LangGraph StateGraph")
    parser.add_argument("--chat", action="store_true", help="Hỏi đáp liên tục cho đến khi gõ exit/quit")
    parser.add_argument("--stream", action="store_true", help="In câu trả lời model theo dạng streaming")
    parser.add_argument("--no-stream", action="store_true", help="Tắt streaming trong chế độ chat")
    parser.add_argument("--model", default=None, help=f"Model name, default {DEFAULT_MODEL} or OPENAI_MODEL")
    parser.add_argument("--base-url", default=None, help=f"OpenAI-compatible base URL, default {DEFAULT_BASE_URL}")
    return parser


def _answer(
    assistant: GPFarmQA,
    query: str,
    use_langgraph: bool,
    history: Optional[Sequence[Dict[str, str]]] = None,
) -> str:
    if _is_greeting(query):
        return GREETING_RESPONSE

    if use_langgraph:
        return assistant.answer_with_graph(query, history=history)
    routed = assistant.classify(query)
    return assistant.answer_with_intent(routed.intent, routed.query, history=history)


def _stream_answer(
    assistant: GPFarmQA,
    query: str,
    history: Optional[Sequence[Dict[str, str]]] = None,
) -> str:
    if _is_greeting(query):
        print(GREETING_RESPONSE, flush=True)
        return GREETING_RESPONSE

    routed = assistant.classify(query)
    chunks: List[str] = []
    for chunk in assistant.stream_answer_with_intent(routed.intent, routed.query, history=history):
        print(chunk, end="", flush=True)
        chunks.append(chunk)
    print()
    return "".join(chunks)


def _chat_loop(assistant: GPFarmQA, use_langgraph: bool, stream: bool) -> None:
    mode = "model" if assistant.client else "offline"
    can_stream_tokens = stream and assistant.client and not use_langgraph
    stream_label = ", streaming" if can_stream_tokens else ""
    print(f"GP Farm Q&A đang sẵn sàng ({mode}{stream_label}). Gõ exit hoặc quit để thoát.")
    history: List[Dict[str, str]] = []
    while True:
        try:
            query = input("\nBạn: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nTạm biệt!")
            break

        if not query:
            continue
        if query.lower() in {"exit", "quit", "q", "thoat", "thoát"}:
            print("Tạm biệt!")
            break

        print("\nGP Farm: ", end="", flush=True)
        if can_stream_tokens:
            answer = _stream_answer(assistant, query, history=history)
        else:
            answer = _answer(assistant, query, use_langgraph, history=history)
            print(answer)
        history.extend(
            [
                {"role": "user", "content": query},
                {"role": "assistant", "content": answer},
            ]
        )


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()
    query = " ".join(args.query).strip()

    assistant = GPFarmQA(model=args.model, base_url=args.base_url, use_llm=not args.offline)
    if args.chat or not query:
        _chat_loop(assistant, args.langgraph, stream=not args.no_stream)
        return

    if args.stream and assistant.client and not args.langgraph:
        _stream_answer(assistant, query)
        return

    print(_answer(assistant, query, args.langgraph))


if __name__ == "__main__":
    main()
