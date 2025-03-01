from io import BytesIO
from RAG.components.model import get_model
import torch
import fitz
from pinecone import Pinecone
from RAG.utils.common import setup_env
import chainlit as cl
from tqdm.auto import tqdm
from RAG.pipeline.stage_01_data_ingestion import DataIngestionPipeLine
from RAG.pipeline.stage_02_search_answer import SearchAnswerPipeline
from RAG.utils.wigets import pc_api, pdf_select, query_type

setup_env()


llm_model = None
from sentence_transformers import SentenceTransformer

embed_model = SentenceTransformer(
    model_name_or_path="all-mpnet-base-v2",
    device="cpu",
)
tokenizer = None

if torch.cuda.is_available():  # which attention version to use
    llm_model, tokenizer, embed_model = get_model()


# @cl.author_rename
# def rename(orig_author: str):
#     rename_dict = {"Chatbot": "VBot"}
#     return rename_dict.get(orig_author, orig_author)


@cl.on_chat_start
async def start():
    msg = cl.Message(content="Hey there! I'm VBot! Ready to assist—what can I do for you today? 🚀",author="Vbot")
    await msg.send()
    # Create settings with the updated select elements
    settings = await cl.ChatSettings(
        [
            # hf_api,
            # model_select,
            pc_api,
            query_type,
            pdf_select,
        ]
    ).send()

    cl.user_session.set("pc", "")
    cl.user_session.set("hf", "")
    cl.user_session.set("model", "Llama-3(gpu)")
    cl.user_session.set("task", "chat")
    cl.user_session.set("paths", {"slot-1": "", "slot-2": "", "slot-3": ""})
    cl.user_session.set("slot", "chat")
    cl.user_session.set("ingester", DataIngestionPipeLine())
    cl.user_session.set(
        "searcher", SearchAnswerPipeline(llm_model, tokenizer, embed_model)
    )
    cl.user_session.set("err", "Setup Api Keys")
    cl.user_session.set("pc_status", False)
    


@cl.on_message
async def on_message(msg: cl.Message):
    print(1)
    query = msg.content
    if not cl.user_session.get("pc_status") and cl.user_session.get("slot") != "chat":
        msg1 = cl.ErrorMessage(content=cl.user_session.get("err"))
        await msg1.send()
        return

    if query == ".pdf":
        await load_pdf_to_pinecone()
        return

    if query == ".data":
        await load_pdf()
        return
    else:
        try:
            print(55)
            searcher = cl.user_session.get("searcher")
            # msg = cl.Message(content="ff")
            # await msg.send()
            if cl.user_session.get("slot") in ["chat","system"]:
                author = "VBot"
            else:
                author = "Rag"
            msg = cl.Message(
                content=searcher.chainlit_prompt(
                    query,
                    cl.user_session.get("task"),
                    cl.user_session.get("hf"),
                    cl.user_session.get("slot"),
                    cl.user_session.get("model"),
                ),
                author=author
            )
            await msg.send()

        except Exception as e:
            msg = cl.Message(content="Error: " + str(e))


async def load_pdf_to_pinecone():
    index_name = cl.user_session.get("slot")
    if index_name in ["chat", "nutrition"]:
        msg = cl.Message(content=f"Can't Upload in {index_name}!")
        await msg.send()
        return
    res = await cl.AskActionMessage(
        content="Ready to Upload!",
        actions=[
            cl.Action(name="continue", value="continue", label="✅ Continue"),
            cl.Action(name="cancel", value="cancel", label="❌ Cancel"),
        ],
    ).send()

    if res and res.get("value") == "continue":
        files = await cl.AskFileMessage(
            content=f"Please upload a PDF file to load in {index_name}, `Please Wait!`",
            accept=["application/pdf"],
            max_size_mb=250,
            timeout=180,
        ).send()

        file = files[0]
        dict = cl.user_session.get("paths")
        dict[index_name] = file.path
        searcher = cl.user_session.get("searcher")
        ingester = cl.user_session.get("ingester")
        cl.user_session.set("paths", dict)
        ingester.load_to_pincone(cl.user_session.get("pc"), file.path, index_name)
        searcher.query_answer.setup_pd(dict)
        msg = cl.Message(content=f"Uploaded to {index_name}! `Start messaging...`")
        await msg.send()


async def load_pdf():
    index_name = cl.user_session.get("slot")
    if index_name in ["chat", "nutrition"]:
        msg = cl.Message(content=f"Can't Upload in {index_name}!")
        await msg.send()
        return
    res = await cl.AskActionMessage(
        content="Ready to Upload!",
        actions=[
            cl.Action(name="continue", value="continue", label="✅ Continue"),
            cl.Action(name="cancel", value="cancel", label="❌ Cancel"),
        ],
    ).send()

    if res and res.get("value") == "continue":
        files = await cl.AskFileMessage(
            content=f"Please upload a PDF file to load in {index_name}, `Please Wait!`",
            accept=["application/pdf"],
            max_size_mb=250,
            timeout=180,
        ).send()

        file = files[0]
        dict = cl.user_session.get("paths")
        dict[index_name] = file.path
        cl.user_session.set("paths", dict)
        ingester = cl.user_session.get("ingester")
        ingester.store_tokens(cl.user_session.get("pc"), file.path, index_name)
        searcher = cl.user_session.get("searcher")
        searcher.query_answer.setup_pd(dict)
        msg = cl.Message(content=f"Uploaded to {index_name}! `Start messaging...`")
        await msg.send()


@cl.on_settings_update
async def verify_keys(settings):
    cl.user_session.set("slot", settings["Pdf"])
    cl.user_session.set("task", settings["Query"])
    if not cl.user_session.get("pc_status"):
        pc = Pinecone(settings["pc_key"])
        try:
            print(pc.list_indexes().names())
            cl.user_session.get("searcher").set_pc(pc)
            cl.user_session.get("ingester").set_pc(pc)
            # cl.user_session.set("pc", settings["pc_key"])
        except:
            message = "Invalid Pinecone Key"
            cl.user_session.set("err", message)
            return
        # cl.user_session.get("searcher").set_pc(pc)
        # import requests

        # API_TOKEN = settings["hf_key"]
        # API_URL = "https://api-inference.huggingface.co/models/gpt2"
        # headers = {"Authorization": f"Bearer {API_TOKEN}"}

        # def query(payload):
        #     response = requests.post(API_URL, headers=headers, json=payload)
        #     return response

        # response = query("Can you please let us know more details about your ")
        # if response.status_code == 400:
        #     message = "Invalid Hugging Face Token"
        #     cl.user_session.set("err", message)
        #     return
        # cl.user_session.set("hf", settings["hf_key"])
        cl.user_session.set("pc_status", True)
        msg = cl.Message(content="All Set 😎!")
        await msg.send()
    # cl.user_session.set("model", settings["Model"])
    
