import re
from fastapi import FastAPI, HTTPException
from typing import List
from pydantic import BaseModel
from models import Resumo, TextoEntrada

app = FastAPI()

resumos: List[Resumo] = []

def markdown_para_texto_simples(markdown: str) -> str:
    """Remove marcações Markdown e retorna texto simples."""
    texto = markdown

    # Remover títulos (#)
    texto = re.sub(r'#+\s?', '', texto)
    # Remover negrito e itálico
    texto = re.sub(r'(\*\*|__)(.*?)\1', r'\2', texto)
    texto = re.sub(r'(\*|_)(.*?)\1', r'\2', texto)
    # Remover listas
    texto = re.sub(r'^[-*+]\s+', '', texto, flags=re.MULTILINE)
    # Remover links [texto](url)
    texto = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', texto)
    # Remover outras marcações
    texto = re.sub(r'[`>]', '', texto)

    return texto.strip()

def gerar_resumo(texto: str) -> str:
    # Remove marcações básicas de Markdown
    texto = re.sub(r'[#*_`\-]+', '', texto)

    # Substitui quebras de linha por espaço simples
    texto = texto.replace('\n', ' ').strip()

    # Separa o texto em frases com base em pontuação final
    frases = re.split(r'(?<=[.!?])\s+', texto)

    # Junta até 3 frases para formar o resumo
    resumo = ' '.join(frases[:3])
    return resumo



@app.post("/resumir/", response_model=Resumo)
def create_resumo(entrada: TextoEntrada):
    if not entrada.texto.strip():
        raise HTTPException(status_code=400, detail="Erro: o texto de entrada está vazio.")

    markdown_texto = entrada.texto
    texto_simples = markdown_para_texto_simples(markdown_texto)

    if not texto_simples:
        raise HTTPException(status_code=400, detail="Erro: formato de entrada inválido.")

    if len(texto_simples) > 3000:
        raise HTTPException(status_code=400, detail="Texto muito longo, reduza para 3000 caracteres.")

    resumo_gerado = gerar_resumo(texto_simples)

    novo_resumo = Resumo(texto=resumo_gerado)
    resumos.append(novo_resumo)
    return novo_resumo

@app.get("/resumos/", response_model=List[Resumo])
def listar_resumos():
    """Retorna a lista de resumos gerados."""
    return resumos
