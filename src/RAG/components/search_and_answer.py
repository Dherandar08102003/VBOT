import os
import re
import requests
import pandas as pd
import numpy
from transformers import AutoTokenizer, AutoModelForCausalLM
from pinecone import Pinecone
import torch

from RAG.entity.config_entity import SearchConfig
from RAG.utils.common import setup_env
from RAG.utils.prompts import PROMPTS, PROMPTS2, PROMPTS3, LLAMA, GEMMA


class SearchAndAnswer:
    def __init__(
        self,
        config: SearchConfig,
        llm_model,
        tokenizer,
        embed_model,
    ) -> None:
        self.config = config
        self.pc = None
        self.embedding_model = embed_model
        nutrition = pd.read_csv(config.data_file)
        nutrition.set_index("index", inplace=True)
        self.dfs = {
            "slot-1": pd.DataFrame(),
            "slot-2": pd.DataFrame(),
            "slot-3": pd.DataFrame(),
            "nutrition": nutrition,
        }
        self.paths = {
            "slot-1": "",
            "slot-2": "",
            "slot-3": "",
            "nutrition": "note",
        }
        if self.config.device_name == "cuda":
            self.chat = LLAMA["system-u"].format(msg="You are a helpful AI assistant")
            self.tokenizer = tokenizer
            self.llm_model = llm_model
        else:
            pass

    def setup_pd(self, paths):
        for slot in paths:
            path = paths[slot]
            if path != "":
                self.dfs[slot] = pd.read_csv(f"{path}.csv")
                self.dfs[slot].set_index("index", inplace=True)
        self.paths = paths

    def retrive_similar_enbeddings(self, query: str, index=None):
        if not index:
            index = self.config.index_name
        index = self.pc.Index(index)
        embeddings = self.embedding_model.encode(query)
        print("embedded")
        query_results = index.query(
            vector=embeddings.tolist(), top_k=self.config.top_k, include_values=True
        )
        # print(4)
        return query_results

    def fetch_chunks(self, query_results, index):
        query_results = query_results["matches"]
        if self.paths[index] != "":
            for item in query_results:
                item["sentence_chunk"] = self.dfs[index].loc[item["id"]][
                    "sentence_chunk"
                ]
            # print(query_results)
            return query_results

    def prompt_formatter(
        self, query: str, context_items: list[dict], base_prompt: str
    ) -> str:
        """
        Augments query with text-based context from context_items.
        """
        # Join context items into one dotted paragraph
        context = "- " + "\n- ".join(
            [
                "Index(" + item["id"] + ")-" + item["sentence_chunk"]
                for item in context_items
            ]
        )

        # Update base prompt with context items and query
        base_prompt = base_prompt.format(context=context, query=query)

        return base_prompt

    def ask_gpu(
        self,
        base_prompt,
        temperature,
        prompt_type,
        max_new_tokens=512,
        format_answer_text=True,
        return_answer_only=True,
    ):
        # Create prompt template for instruction-tuned model
        # dialogue_template = [{"role": "user", "content": base_prompt}]
        # # Apply the chat template
        # prompt = self.tokenizer.apply_chat_template(
        #     conversation=dialogue_template, tokenize=False, add_generation_prompt=True
        # )
        # Tokenize the prompt
        input_ids = self.tokenizer(base_prompt, return_tensors="pt").to(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        # Generate an output of tokens
        outputs = self.llm_model.generate(
            **input_ids,
            temperature=temperature,
            do_sample=True,
            max_new_tokens=max_new_tokens,
        )

        # Turn the output tokens into text
        output_text = self.tokenizer.decode(outputs[0])
        if prompt_type == "chat":
            self.chat = output_text
        if format_answer_text:
            # Replace special tokens and unnecessary help message
            output_text = (
                output_text.replace(base_prompt, "")
                .replace(base_prompt, "")
                .replace("<|begin_of_text|>", "")
            )

        # Only return the answer without the context items
        if return_answer_only:
            return output_text.replace("<|eot_id|>", "")

        return

    def ask_cpu(self, base_prompt, temperature, hf_key, model, max_new_tokens=512):
        API_URL = f"https://api-inference.huggingface.co/models/{model}"
        API_TOKEN = hf_key
        if "gemma" in model:
            base_prompt = GEMMA["user"].format(msg=base_prompt)
        payload = {
            "inputs": base_prompt,
            "parameters": {
                "temperature": temperature,
                "return_full_text": False,
            },
            "options": {"wait_for_model": True},
        }
        headers = {"Authorization": f"Bearer {API_TOKEN}"}
        response = requests.post(API_URL, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code}")
            print(response.json())
            return [{"generated_text":"None"}]

    def ask(self, query, context_items, prompt_type, hf_key, model, index):
        context = "- " + "\n- ".join(
            [
                "Index[" + item["id"] + "]-" + item["sentence_chunk"]
                for item in context_items
            ]
        )
        if self.config.device_name == "cuda" and model == "Llama-3(gpu)":
            if index == "chat":
                if prompt_type == "system":
                    self.chat = ""
                if prompt_type not in ["chat", "system"]:
                    return "currently chat or system is suported for llama 3 gpu"
                prompt = LLAMA[prompt_type].format(msg=query)
                self.chat += prompt
                answer = self.ask_gpu(self.chat, 1, prompt_type)
            else:
                prompt_set = PROMPTS[prompt_type]
                base_prompt = prompt_set["prompt"].format(context=context, query=query)
                prompt = (
                    LLAMA["system"].format(msg="You are a helpful AI assistant")
                    + "\n\n"
                    + LLAMA["user"].format(msg=base_prompt)
                )
                answer = self.ask_gpu(prompt, prompt_set["temperature"], prompt_type)
            return answer
        elif prompt_type != "system" and model != "Llama-3(gpu)":
            prompt_set = PROMPTS[prompt_type]
            base_prompt = prompt_set["prompt"].format(context=context, query=query)
            answer = self.ask_cpu(base_prompt, prompt_set["temperature"], hf_key, model)
            return answer[0]["generated_text"].replace("Answer:", "")
        else:
            return "Some unknown error in settings"

    def ask1(self, query, context_items, prompt_type, hf_key, model, index):
        if (
            index == "chat"
            and self.config.device_name == "cuda"
            and model == "Llama-3(gpu)"
        ):
            if prompt_type == "system":
                self.chat = ""
            if prompt_type not in ["chat", "system"]:
                return "currently chat or system is suported for llama 3 gpu"
            prompt = LLAMA[prompt_type].format(msg=query)
            self.chat += prompt
            prompt_set = {"prompt": self.chat, "temperature": 1}
            answer = self.ask_gpu(self.chat, "", prompt_set["temperature"])
            return answer
        elif prompt_type != "system" and model != "Llama-3(gpu)":
            if prompt_type == "system":
                return "system message cant be modified!"
            prompt_set = PROMPTS[prompt_type]
            context = "- " + "\n- ".join(
                [
                    "Index[" + item["id"] + "]-" + item["sentence_chunk"]
                    for item in context_items
                ]
            )

            # Update base prompt with context items and query
            base_prompt = prompt_set["prompt"].format(context=context, query=query)
            base_prompt = self.clean_prompt(base_prompt)
            if model == "Llama-3(gpu)" and self.config.device_name == "cuda":
                base_prompt = (
                    LLAMA["system"].format(msg="You are a helpful AI assistant")
                    + "\n\n"
                    + LLAMA["user"].format(msg=base_prompt)
                )
        if self.config.device_name == "cuda" and model == "Llama-3(gpu)":
            answer = self.ask_gpu(base_prompt,"", prompt_set["temperature"])
        elif model != "Llama-3(gpu)":
            answer = self.ask_cpu(base_prompt, prompt_set["temperature"], hf_key, model)
        else:
            answer = (
                "Your Instruction setting is Wrong! eg: selecting gpu model without gpu"
            )
        return answer

    def clean_prompt(self, prompt):
        # Remove leading and trailing spaces
        # prompt = prompt.strip()

        # Replace multiple spaces with a single space
        prompt = re.sub(r"\s+", " ", prompt)

        # Remove all special characters except letters, digits, and basic punctuation
        # Allowed characters: a-z, A-Z, 0-9, space, and basic punctuation (.,!?')
        allowed_characters = re.compile(r'^a-zA-Z0-9\s.,!?\]\[\'"-')

        # Remove characters that are not in the allowed set
        cleaned_prompt = allowed_characters.sub("", prompt)
        return cleaned_prompt

    def err_msg(self, msg):
        return [{"generated_text": msg}]
