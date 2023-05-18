import streamlit as st
import unicodedata
import diff_match_patch as dmp_module
from enum import Enum

import openai
import dotenv
import os

dotenv.load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

system_prompt = """
あなたは文書を校正するアシスタントです。
"""

prompt = """
あなたは文書を校正するアシスタントです。
意味を変えない前提で、与えられた文章を訂正して出力してください。
英語で書かれている単語をそのまましてください。
修正のポイントは以下です。
1. 誤字脱字
2. 文法の誤り
3. 不自然な表現

例:
===訂正前の文章開始===
昨日は10時に寝った。
「風邪は治った？」「はい、もう元気から大丈夫です」
===訂正前の文章終了===
訂正後の文章:
昨日は10時に寝た。
「風邪は治った？」「はい、もう元気だから大丈夫です」

以下の文章を訂正してください。
===訂正前の文章開始===
{passage}
===訂正前の文章終了===
訂正後の文章:"""



class Action(Enum):
    INSERTION = 1
    DELETION = -1
    EQUAL = 0

def compare_string(text1:str, text2: str) -> list:
    text1Normalized = unicodedata.normalize("NFKC", text1)
    text2Normalized = unicodedata.normalize("NFKC", text2)

    dmp = dmp_module.diff_match_patch()
    diff = dmp.diff_main(text1Normalized, text2Normalized)
    dmp.diff_cleanupSemantic(diff)

    return diff

def style_text(diff):
    fullText=""
    for action, text in diff:
        if action == Action.INSERTION.value:
            fullText += f"<span style='background-color:Lightgreen'>{text}</span>"
        elif action == Action.DELETION.value:
            fullText += f"<span style='background-color:#FFCCCB'><s>{text}</s></span>"
        elif action == Action.EQUAL.value:
            fullText += f"{text}"
        else:
            raise Exception("Not Implemented")
    fullText = fullText.replace('](', ']\(').replace('~', '\~')
    return fullText

if __name__=="__main__":
    st.title("日本語文書校正アシスタント")
    option = st.selectbox(
        '使うモデルを選択してください',
        ("gpt-3.5-turbo", 'gpt-4')
    )
    orig_txt = st.text_area("Input Text", height=200
    )
    fixed_txt = ""
    if orig_txt:
        output = openai.ChatCompletion.create(
        model=option,
        messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt.format(passage=orig_txt)},
            ],
        stream=True,
        )
        st.write("---")
        st.write("Fixed Text")
        result_area = st.empty()
        
        
        fixed_txt = ""
        for chunk in output:
            next = chunk['choices'][0]['delta'].get('content', '')
            fixed_txt += next
            result_area.write(fixed_txt)                        
        st.write("---")
        st.write("Text Diff")
        diff = compare_string(orig_txt, fixed_txt)
        fullText = style_text(diff)
        st.write(fullText, unsafe_allow_html=True)