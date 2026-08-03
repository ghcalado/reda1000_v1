"""
ocr.py — Modulo de extracao de texto de imagens de redacoes manuscritas.
Utiliza o modelo de visao da Groq (LLaMA 3.2 Vision) para transcrever
caligrafias em texto plano, mantendo paragrafos e estrutura originais.
"""

import base64
import logging
import os
import time

from groq import Groq

from app.config import GROQ_API_KEY, GROQ_VISION_MODEL, validar_configuracoes

logger = logging.getLogger(__name__)

PROMPT_TRANSCRICAO = """Voce e um sistema de OCR especializado em redacoes manuscritas do ENEM.

INSTRUCOES RIGOROSAS:
1. Transcreva o texto manuscrito da imagem com a maior fidelidade possivel.
2. Mantenha a separacao exata de paragrafos como escrita pelo aluno.
3. Corrija apenas erros que sejam claramente de OCR (leitura errada), NAO corrija
   erros ortograficos ou gramaticais do aluno — eles fazem parte da avaliacao.
4. Se uma palavra for absolutamente ilegivel, insira [ilegivel] no lugar.
5. Retorne APENAS o texto transcrito, sem comentarios, titulos ou explicacoes."""

EXTENSOES_SUPORTADAS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}


class ExtratorVisao:
    def __init__(self) -> None:
        logger.info("Inicializando modulo de visao (Groq Vision)...")
        validar_configuracoes()
        self.client = Groq(api_key=GROQ_API_KEY, timeout=60, max_retries=2)
        self.modelo = GROQ_VISION_MODEL

    def _codificar_imagem(self, caminho_imagem: str) -> str:
        caminho_abs = os.path.abspath(caminho_imagem)

        if not os.path.isfile(caminho_abs):
            raise FileNotFoundError(f"Arquivo nao encontrado: {caminho_abs}")

        extensao = os.path.splitext(caminho_abs)[1].lower()
        if extensao not in EXTENSOES_SUPORTADAS:
            raise ValueError(
                f"Formato '{extensao}' nao suportado. "
                f"Use: {', '.join(sorted(EXTENSOES_SUPORTADAS))}"
            )

        tamanho_mb = os.path.getsize(caminho_abs) / (1024 * 1024)
        if tamanho_mb > 20:
            raise ValueError(
                f"Imagem muito grande ({tamanho_mb:.1f} MB). Maximo: 20 MB."
            )

        with open(caminho_abs, "rb") as f:
            dados = f.read()

        logger.info(
            "Imagem carregada: %s (%.2f MB)",
            os.path.basename(caminho_abs), tamanho_mb
        )
        return base64.b64encode(dados).decode("utf-8")

    def _detectar_mime(self, caminho_imagem: str) -> str:
        extensao = os.path.splitext(caminho_imagem)[1].lower()
        mapa = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
            ".gif": "image/gif",
            ".bmp": "image/bmp",
        }
        return mapa.get(extensao, "image/jpeg")

    def transcrever(self, caminho_imagem: str) -> str:
        logger.info("Iniciando transcricao da imagem: %s", caminho_imagem)
        inicio = time.time()

        base64_img = self._codificar_imagem(caminho_imagem)
        mime_type = self._detectar_mime(caminho_imagem)

        try:
            resposta = self.client.chat.completions.create(
                model=self.modelo,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": PROMPT_TRANSCRICAO,
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{base64_img}"
                                },
                            },
                        ],
                    }
                ],
                temperature=0.1,
                max_tokens=4096,
            )

            texto = resposta.choices[0].message.content.strip()
            duracao = time.time() - inicio

            logger.info(
                "Transcricao concluida em %.2f segundos (%d caracteres extraidos).",
                duracao, len(texto)
            )
            return texto

        except Exception as e:
            logger.error("Erro na transcricao por visao: %s", e)
            raise RuntimeError(f"Falha ao transcrever a imagem: {e}") from e
