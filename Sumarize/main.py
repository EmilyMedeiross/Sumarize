import re
from fastapi import FastAPI, HTTPException, Depends, Request
from typing import List, Annotated
from models import Resumo, TextoEntrada, PalavrasChaveResposta, PalavraChave, ResumoPalavra
from fastapi.responses import Response, PlainTextResponse
from fastapi.exceptions import RequestValidationError
from sqlmodel import SQLModel, Session, select, create_engine
from contextlib import asynccontextmanager

url = "sqlite:///sumarize.db"
args = {"check_same_thread": False }
engine = create_engine(url, connect_args=args)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

def criar_db_e_tabelas():
    SQLModel.metadata.create_all(engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    criar_db_e_tabelas()
    yield

app = FastAPI(lifespan=lifespan)

#Lista de palavras que serão ignoradas na contagem de palavras-chave
# Coloquei isso para filtrar conectivos e artigos
IGNORE_WORDS = {
    "o", "a", "os", "as", "um", "uma", "uns", "umas", "de", "do", "da", "dos", "das",
    "em", "no", "na", "nos", "nas", "por", "para", "com", "sem", "que", "e", "é"
}

#Função para limpar marcações Markdown do texto 
#Isso está sendo usado porque o texto de entrada pode vir com formatação
def markdown_para_texto(markdown: str) -> str:

    if not markdown:
        return ""
    
    substituicoes = [
        (r'#+\s?', ''), 
        (r'(\*\*|__)(.*?)\1', r'\2'), 
        (r'(\*|_)(.*?)\1', r'\2'), 
        (r'^[-*+]\s+', ''), 
        (r'\[(.*?)\]\(.*?\)', r'\1'), 
        (r'[`>]', '')
    ]
    texto = markdown

    for padrao, substituicao in substituicoes:
        texto = re.sub(padrao, substituicao, texto, flags=re.MULTILINE)
    return texto.strip()

#Função que pega as 3 primeiras frases do texto, como se fosse um resumo simples
def gerar_resumo(texto: str) -> str:
    texto = re.sub(r'[#*_`\-]+', '', texto)
    texto = texto.replace('\n', ' ').strip()
    frases = re.split(r'(?<=[.!?])\s+', texto)
    return ' '.join(frases[:3])

#Extrai as palavras-chave com base em frequência, sem usar bibliotecas
def palavras_chave_texto(texto: str) -> List[str]:
    if not texto:
        return []
    texto_limpo = re.sub(r'[^\w\s]', '', texto.lower())
    palavras = texto_limpo.split()

    contador = {}
    for palavra in palavras:
        if palavra not in IGNORE_WORDS:
            contador[palavra] = contador.get(palavra, 0) + 1
            
    palavras_ordenadas = sorted(contador.items(), key=lambda x: x[1], reverse=True)

    return [palavra.capitalize() for palavra, _ in palavras_ordenadas[:5]]

#Essa função serve para criar resposta personalizada em XML
def formatar_resposta_xml(resumo: str, palavras_chave: List[str]) -> str:
    resumo_xml = f"<resumo>{resumo}</resumo>" if resumo else "<resumo />"
    palavras_xml = "".join(f"<palavra>{p}</palavra>" for p in palavras_chave)
    palavras_chave_xml = f"<palavras-chave>{palavras_xml}</palavras-chave>" if palavras_xml else "<palavras-chave />"
    return f"<resposta>{resumo_xml}{palavras_chave_xml}</resposta>"

#Essa função salva as palavras-chave relacionadas ao resumo 
#Aqui faz um relacionamento N:N entre Resumo e Palavras-Chave 
def salvar_palavras_chave(session: Session, resumo_id: int, palavras: List[str]):
    for palavra in palavras:
        palavra_lower = palavra.lower()
        db_palavra = session.exec(select(PalavraChave).where(PalavraChave.termo == palavra_lower)).first()

        if not db_palavra:
            db_palavra = PalavraChave(termo=palavra_lower)
            session.add(db_palavra)
            session.commit()
            session.refresh(db_palavra)

        relacao = ResumoPalavra(resumo_id=resumo_id, palavra_id=db_palavra.id, frequencia=1)
        session.add(relacao)
    session.commit()

@app.post("/processar/", response_class=PlainTextResponse, response_model=None)
def processar_texto(entrada: TextoEntrada):

    try:
        if not entrada.texto.strip():
            raise HTTPException(status_code=400, detail="Erro: o texto de entrada está vazio.")
        
        texto_simples = markdown_para_texto(entrada.texto)
        resumo = gerar_resumo(texto_simples)
        palavras = palavras_chave_texto(texto_simples)

        return PlainTextResponse(content=formatar_resposta_xml(resumo, palavras), media_type="application/xml")
    
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Erro Interno")

@app.post("/resumir/", response_model=Resumo)
def criar_resumo(entrada: TextoEntrada, session: SessionDep):
    texto_simples = markdown_para_texto(entrada.texto)

    if not texto_simples:
        raise HTTPException(status_code=400, detail="Erro: Texto Inválido")
    
    resumo_gerado = gerar_resumo(texto_simples)
    palavras = palavras_chave_texto(texto_simples)
    novo_resumo = Resumo(texto=resumo_gerado)

    session.add(novo_resumo)
    session.commit()
    session.refresh(novo_resumo)
    salvar_palavras_chave(session, novo_resumo.id, palavras)
    return novo_resumo

@app.get("/resumos/", response_model=List[Resumo])
def listar_resumos(session: SessionDep):
    
    return session.exec(select(Resumo)).all()

@app.get("/resumos/{resumo_id}/palavras-chave", response_model=PalavrasChaveResposta)
def obter_palavras_chave(resumo_id: int, session: SessionDep):
    resumo = session.get(Resumo, resumo_id)

    if not resumo:
        raise HTTPException(status_code=404, detail="Resumo não encontrado")
    
    palavras = [p.termo.capitalize() for p in resumo.palavras_chave]
    return PalavrasChaveResposta(palavras=palavras)

@app.post("/palavras-chaves/", response_model=PalavrasChaveResposta)
def extrair_palavras_chave(entrada: TextoEntrada):
    texto_simples = markdown_para_texto(entrada.texto)
    palavras = palavras_chave_texto(texto_simples)

    if not palavras:
        raise HTTPException(status_code=400, detail="Erro: não foi possível extrair palavras-chave do texto.")
    
    return PalavrasChaveResposta(palavras=palavras)

@app.put("/resumos/{resumo_id}", response_model=Resumo)
def atualizar_resumo(resumo_id: int, entrada: TextoEntrada, session: SessionDep):
    resumo = session.get(Resumo, resumo_id)

    if not resumo:
        raise HTTPException(status_code=404, detail="Resumo não encontrado")

    texto_simples = markdown_para_texto(entrada.texto)
    resumo.texto = gerar_resumo(texto_simples)

    session.add(resumo)
    session.commit()
    session.refresh(resumo)

    # Aqui estou limpando as relações antigas antes de salvar as novas palavras
    relacoes_antigas = session.exec(select(ResumoPalavra).where(ResumoPalavra.resumo_id == resumo_id)).all()

    for rel in relacoes_antigas:
        session.delete(rel)
    session.commit()

    palavras = palavras_chave_texto(texto_simples)
    salvar_palavras_chave(session, resumo_id, palavras)
    return resumo

@app.delete("/resumos/{resumo_id}")
def deletar_resumo(resumo_id: int, session: SessionDep):

    resumo = session.get(Resumo, resumo_id)
    if not resumo:
        raise HTTPException(status_code=404, detail="Resumo não encontrado")
    
    session.delete(resumo)
    session.commit()
    return {"message": "Resumo deletado com sucesso"}

# Essa parte é um tratamneto personalizado do erro 422
# Fiz isso para retornar XML em vez de JSON quando há um erro na entrada 

@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    details = [f"{err['msg']} ({'.'.join(str(x) for x in err['loc'])})" for err in errors]

    return Response(
        content=f"<erro>{'; '.join(details)}</erro>",
        media_type="application/xml",
        status_code=422
    )
