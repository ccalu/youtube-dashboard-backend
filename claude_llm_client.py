"""
Claude CLI Client — chama Claude via CLI local usando tokens do plano Max.

Padrao baseado em content_factory_v3/shared/processors/bloco3_orchestrator.py
Requer: Claude Code instalado (npm i -g @anthropic-ai/claude-code) + Max logado.
"""

import json
import logging
import os
import shutil
import subprocess
import time

logger = logging.getLogger(__name__)

SDK_CALL_TIMEOUT_S = 600  # 10 minutos


def is_claude_cli_available() -> bool:
    """Verifica se o Claude CLI esta no PATH."""
    return shutil.which("claude") is not None


def call_claude_cli(
    system_prompt: str,
    user_prompt: str,
    model: str = "claude-opus-4-6",
    timeout: int = SDK_CALL_TIMEOUT_S,
) -> str:
    """
    Chama Claude CLI como subprocesso sincrono. Retorna texto da resposta.

    Args:
        system_prompt: Instrucoes do sistema
        user_prompt: Prompt do usuario com dados
        model: ID do modelo (default: claude-opus-4-6)
        timeout: Timeout em segundos

    Returns:
        Texto da resposta do Claude

    Raises:
        RuntimeError: Se CLI nao encontrado, timeout, ou erro
    """
    cli_path = shutil.which("claude")
    if not cli_path:
        raise RuntimeError(
            "Claude CLI nao encontrado no PATH. "
            "Instale: npm i -g @anthropic-ai/claude-code"
        )

    # Montar comando base (sem tools, single-turn)
    cmd = [
        cli_path,
        "--print",
        "--verbose",
        "--output-format", "stream-json",
        "--input-format", "stream-json",
        "--model", model,
        "--max-turns", "1",
        "--allowedTools", "",
        "--permission-mode", "acceptEdits",
        "--setting-sources", "",
    ]

    # Windows: limite 32K chars no cmd. Se system_prompt cabe, passa via --system-prompt.
    cmd_base_len = sum(len(a) for a in cmd) + len(cmd)
    max_system_len = 32767 - cmd_base_len - 1500

    if len(system_prompt) < max_system_len:
        cmd.extend(["--system-prompt", system_prompt])
        effective_prompt = user_prompt
    else:
        cmd.extend(["--system-prompt", "Follow the instructions in my message carefully."])
        effective_prompt = (
            f"=== SYSTEM INSTRUCTIONS ===\n\n{system_prompt}\n\n"
            f"=== END SYSTEM INSTRUCTIONS ===\n\n"
            f"=== USER REQUEST ===\n\n{user_prompt}"
        )
        logger.debug(f"System prompt muito longo ({len(system_prompt)} chars), enviando via stdin")

    # Montar mensagem stream-json
    input_message = json.dumps({
        "type": "user",
        "session_id": "",
        "message": {"role": "user", "content": effective_prompt},
        "parent_tool_use_id": None,
    }) + "\n"

    # Preparar environment
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    env["CLAUDE_CODE_ENTRYPOINT"] = "sdk-py"

    start_time = time.time()
    logger.info(f"[claude-cli] Chamando modelo={model}, prompt={len(effective_prompt)} chars")

    # Executar como subprocesso sincrono
    try:
        result = subprocess.run(
            cmd,
            input=input_message.encode("utf-8"),
            capture_output=True,
            timeout=timeout,
            env=env,
        )
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        logger.error(f"[claude-cli] TIMEOUT apos {elapsed:.0f}s (limite={timeout}s)")
        raise RuntimeError(f"Claude CLI timeout apos {elapsed:.0f}s")

    elapsed = time.time() - start_time
    stdout_bytes = result.stdout
    stderr_bytes = result.stderr

    # Parsear resposta stream-json
    text_parts = []
    input_tokens = 0
    output_tokens = 0

    if stdout_bytes:
        for line in stdout_bytes.decode("utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue

            msg_type = data.get("type")

            if msg_type == "assistant":
                for block in data.get("message", {}).get("content", []):
                    if block.get("type") == "text":
                        text_parts.append(block["text"])

            elif msg_type == "result":
                usage = data.get("usage", {})
                if usage:
                    input_tokens = usage.get("input_tokens", 0)
                    output_tokens = usage.get("output_tokens", 0)
                    input_tokens += usage.get("cache_creation_input_tokens", 0)
                    input_tokens += usage.get("cache_read_input_tokens", 0)
                # Tambem captura texto do result
                result_text = data.get("result", "")
                if result_text and not text_parts:
                    text_parts.append(result_text)

    # Verificar erros
    if result.returncode != 0 and not text_parts:
        stderr_text = stderr_bytes.decode("utf-8", errors="replace") if stderr_bytes else ""
        raise RuntimeError(
            f"Claude CLI saiu com codigo {result.returncode}. "
            f"stderr: {stderr_text[:500]}"
        )

    # Detectar ghost response (0 tokens)
    if input_tokens == 0 and output_tokens == 0 and not text_parts:
        raise RuntimeError(
            f"Claude CLI ghost: 0 tokens apos {elapsed:.0f}s "
            f"(rc={result.returncode})"
        )

    text = "".join(text_parts)
    logger.info(
        f"[claude-cli] OK modelo={model} "
        f"in={input_tokens} out={output_tokens} "
        f"duracao={elapsed:.1f}s chars={len(text)}"
    )
    return text
