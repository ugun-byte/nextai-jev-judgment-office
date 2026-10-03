"""
NextAI Commercial Frontier AI (GPT-4o, Claude, Gemini, OpenRouter) Integration Service
Handles fallback reasoning for unfamiliar, novel, or ambiguous issues when System 1 (Jev/Local AI) is uncertain.
"""

import json
import urllib.request
import urllib.error
import time

def test_ai_connection(provider, api_key, model=None):
    """
    Test connection and validate API key for the chosen provider.
    """
    provider = (provider or "gemini").lower()
    api_key = (api_key or "").strip()
    
    if not api_key:
        return {"ok": False, "error": "API 키가 입력되지 않았습니다."}
    
    start_time = time.time()
    
    try:
        # 1. Google Gemini
        if provider == "gemini":
            mod = model or "gemini-1.5-flash"
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{mod}:generateContent?key={api_key}"
            payload = {
                "contents": [{"parts": [{"text": "Reply with JSON: {\"status\":\"ok\"}"}]}],
                "generationConfig": {"temperature": 0.1}
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                elapsed = int((time.time() - start_time) * 1000)
                return {"ok": True, "provider": "Google Gemini", "model": mod, "elapsedMs": elapsed, "message": "Google Gemini API 연결 성공!"}
        
        # 2. OpenAI
        elif provider == "openai":
            mod = model or "gpt-4o-mini"
            url = "https://api.openai.com/v1/chat/completions"
            payload = {
                "model": mod,
                "messages": [{"role": "user", "content": "Reply with 'ok'"}],
                "max_tokens": 5
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                }
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                elapsed = int((time.time() - start_time) * 1000)
                return {"ok": True, "provider": "OpenAI", "model": mod, "elapsedMs": elapsed, "message": "OpenAI API 연결 성공!"}
        
        # 3. Anthropic Claude
        elif provider == "claude":
            mod = model or "claude-3-5-haiku-20241022"
            url = "https://api.anthropic.com/v1/messages"
            payload = {
                "model": mod,
                "max_tokens": 10,
                "messages": [{"role": "user", "content": "Reply with 'ok'"}]
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01"
                }
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                elapsed = int((time.time() - start_time) * 1000)
                return {"ok": True, "provider": "Anthropic Claude", "model": mod, "elapsedMs": elapsed, "message": "Anthropic Claude API 연결 성공!"}
        
        # 4. OpenRouter / Custom OpenAI Compatible
        elif provider in ["openrouter", "deepseek"]:
            mod = model or "meta-llama/llama-3.2-3b-instruct:free"
            url = "https://openrouter.ai/api/v1/chat/completions"
            payload = {
                "model": mod,
                "messages": [{"role": "user", "content": "Reply with 'ok'"}],
                "max_tokens": 5
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                }
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                elapsed = int((time.time() - start_time) * 1000)
                return {"ok": True, "provider": "OpenRouter", "model": mod, "elapsedMs": elapsed, "message": "OpenRouter API 연결 성공!"}
        
        else:
            return {"ok": False, "error": f"지원되지 않는 AI 제공자입니다: {provider}"}
            
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8")
        except Exception:
            pass
        return {"ok": False, "error": f"HTTP {e.code} 오류: {e.reason}\n{body[:200]}"}
    except Exception as e:
        return {"ok": False, "error": f"연결 실패: {str(e)}"}


def solve_unfamiliar_issue(provider, api_key, model, mail_subject, mail_body, question_id, question_def):
    """
    Sends unfamiliar/ambiguous customer inquiry to commercial frontier LLM for deep reasoning and resolution.
    Returns structured choice, confidence, reasoning explanation, and auto-draft reply.
    """
    provider = (provider or "gemini").lower()
    api_key = (api_key or "").strip()
    start_time = time.time()
    
    # Construct System Prompt & Guidance
    options_summary = []
    criteria = question_def.get("criteria", {})
    if isinstance(criteria, dict):
        for k, v in criteria.items():
            options_summary.append(f"- '{k}': {v}")
    elif isinstance(criteria, list):
        for idx, desc in enumerate(criteria):
            options_summary.append(f"- Level {idx}: {desc}")

    prompt = f"""You are the Executive AI Chief Operations Officer of a premier AI EdTech company ('NextAI').
Our local frontline model was uncertain about the following complex, unfamiliar, or ambiguous customer inquiry:

[Incoming Customer Inquiry]
Subject: {mail_subject}
Body: {mail_body}

[Current Decision Question to Solve]
Question ID: {question_id}
Title: {question_def.get('nameKo', question_id)}
Instructions: {question_def.get('instructions', '')}

[Available Options & Criteria]
{chr(10).join(options_summary)}

Please deeply analyze the subtle context, customer intent, business risk, and strategic implications.
Output ONLY a strict JSON object with:
{{
  "choice": "<the exact chosen key, e.g. 'billing', 'technical', 'partnership', 'mentoring', 'archive_noise', or level string>",
  "confidence": <float between 0.90 and 0.99>,
  "reasoning": "<1-2 sentences in Korean explaining why this choice is strategically optimal for NextAI>",
  "draft_reply": "<Polite, highly professional Korean customer reply addressing their specific novel problem>"
}}"""

    # If simulation / no key provided, return high quality simulated reasoning
    if not api_key:
        content_lower = f"{mail_subject} {mail_body}".lower()
        chosen_key = list(criteria.keys())[0] if isinstance(criteria, dict) else "0"
        reasoning_text = "상용 AI 심층 추론: 고객의 복합 문의 맥락을 심층 분석하여 최적의 부서로 책임 배정하였습니다."
        draft_text = f"안녕하세요 수강생님, NextAI 대표이사 운영본부입니다. 문의주신 사항('{mail_subject}')을 신속히 검토하였으며, 담당 전문 부서에서 우선순위로 지원해 드리겠습니다."

        if isinstance(criteria, dict):
            if any(w in content_lower for w in ["환불", "결제", "취소", "영수증", "승인", "계좌", "금액"]):
                if "billing" in criteria:
                    chosen_key = "billing"
                    reasoning_text = "고객의 문의에 환불 및 결제 관련 금전적 요구가 직접 포함되어 있어, 최우선적으로 재무/결제팀의 긴급 검토와 약관 확인이 필요하다고 판단했습니다."
                    draft_text = "안녕하세요 수강생님, NextAI 결제/환불 지원팀입니다. 문의주신 결제 및 환불 관련 요청 건을 접수하였으며, 수강 진도율 및 이용약관에 따른 즉시 처리 방안을 안내해 드리겠습니다."
            elif any(w in content_lower for w in ["동업", "제안", "스폰서", "광고", "협찬", "출강", "특강", "협력", "b2b", "계약"]):
                if "partnership" in criteria:
                    chosen_key = "partnership"
                    reasoning_text = "단순 문의를 넘어 신규 비즈니스 제휴, 동업 제안 또는 기업 협력 기회가 포함된 전략적 안건으로 판단되어 대외협력/제휴팀으로 배정했습니다."
                    draft_text = "안녕하세요, NextAI 비즈니스 제휴팀입니다. 제안해주신 협업 및 파트너십 제안에 깊은 감사를 드립니다. 대표이사 및 실무진 검토 후 구체적인 협의 일정을 회신드리겠습니다."
            elif any(w in content_lower for w in ["오류", "버그", "에러", "cuda", "코드", "서버", "접속", "라이선스"]):
                if "technical" in criteria:
                    chosen_key = "technical"
                    reasoning_text = "기술적 오류 해결, 소스코드 라이선스 검증 또는 시스템 환경 설정이 직결된 전문 기술 이슈로 판단하여 기술지원 엔지니어팀으로 배정했습니다."
                    draft_text = "안녕하세요 수강생님, NextAI 기술지원팀입니다. 제보해 주신 기술적 문제 및 소스코드 관련 세부 내역을 확인 중에 있으며, 엔지니어 정밀 분석 후 조속히 해결책을 안내해 드리겠습니다."
            elif any(w in content_lower for w in ["개념", "수식", "attention", "이해", "질문", "공부", "강의내용"]):
                if "mentoring" in criteria:
                    chosen_key = "mentoring"
                    reasoning_text = "강의 커리큘럼 및 AI 수식 이해에 관한 심화 학습 질문으로 분류되어 전담 학습 멘토링 연구원에게 배정했습니다."
                    draft_text = "안녕하세요 수강생님, NextAI 수석 튜터입니다. 질문해 주신 수식 및 알고리즘 원리에 대해 핵심 개념과 추가 참고자료를 정리하여 안내해 드립니다."
            elif any(w in content_lower for w in ["광고", "출간", "예약판매", "키보드", "잡담"]):
                if "archive_noise" in criteria:
                    chosen_key = "archive_noise"
                    reasoning_text = "단방향 홍보, 스팸성 메일 또는 단순 잡담성 문의로 판단되어 실무진의 업무 집중을 위해 스마트 보관함으로 자동 분류하였습니다."
                    draft_text = "감사합니다. NextAI 운영센터에 안전하게 접수 및 보관되었습니다."

        return {
            "ok": True,
            "simulated": True,
            "provider": f"{provider.upper()} (체험 시뮬레이션)",
            "model": model or "frontier-reasoning",
            "choice": chosen_key,
            "confidence": 0.96,
            "reasoning": reasoning_text,
            "draft_reply": draft_text,
            "elapsedMs": 420
        }

    try:
        # Call Google Gemini
        if provider == "gemini":
            mod = model or "gemini-1.5-flash"
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{mod}:generateContent?key={api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.2,
                    "responseMimeType": "application/json"
                }
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
                text = raw["candidates"][0]["content"]["parts"][0]["text"]
                parsed = json.loads(text)
                elapsed = int((time.time() - start_time) * 1000)
                return {
                    "ok": True,
                    "simulated": False,
                    "provider": "Google Gemini",
                    "model": mod,
                    "choice": parsed.get("choice"),
                    "confidence": float(parsed.get("confidence", 0.95)),
                    "reasoning": parsed.get("reasoning", "Gemini 심층 분석 완료"),
                    "draft_reply": parsed.get("draft_reply", ""),
                    "elapsedMs": elapsed
                }
        
        # Call OpenAI
        elif provider == "openai":
            mod = model or "gpt-4o-mini"
            url = "https://api.openai.com/v1/chat/completions"
            payload = {
                "model": mod,
                "messages": [
                    {"role": "system", "content": "You are a professional business operations AI. Always output valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.2
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                }
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
                text = raw["choices"][0]["message"]["content"]
                parsed = json.loads(text)
                elapsed = int((time.time() - start_time) * 1000)
                return {
                    "ok": True,
                    "simulated": False,
                    "provider": "OpenAI",
                    "model": mod,
                    "choice": parsed.get("choice"),
                    "confidence": float(parsed.get("confidence", 0.96)),
                    "reasoning": parsed.get("reasoning", "GPT-4o 심층 분석 완료"),
                    "draft_reply": parsed.get("draft_reply", ""),
                    "elapsedMs": elapsed
                }

        # Call Anthropic Claude
        elif provider == "claude":
            mod = model or "claude-3-5-haiku-20241022"
            url = "https://api.anthropic.com/v1/messages"
            payload = {
                "model": mod,
                "max_tokens": 1024,
                "system": "You are a professional business operations AI. Output strict JSON only.",
                "messages": [{"role": "user", "content": prompt}]
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01"
                }
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
                text = raw["content"][0]["text"]
                # Parse JSON out of markdown block if wrapped
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0].strip()
                parsed = json.loads(text)
                elapsed = int((time.time() - start_time) * 1000)
                return {
                    "ok": True,
                    "simulated": False,
                    "provider": "Anthropic Claude",
                    "model": mod,
                    "choice": parsed.get("choice"),
                    "confidence": float(parsed.get("confidence", 0.97)),
                    "reasoning": parsed.get("reasoning", "Claude 3.5 심층 분석 완료"),
                    "draft_reply": parsed.get("draft_reply", ""),
                    "elapsedMs": elapsed
                }

    except Exception as e:
        return {"ok": False, "error": f"상용 AI 연동 오류: {str(e)}"}

    return {"ok": False, "error": "지원되지 않는 제공자 또는 설정 오류"}
