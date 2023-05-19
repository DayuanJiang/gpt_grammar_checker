import streamlit as st
import unicodedata
import diff_match_patch as dmp_module
from enum import Enum
from langdetect import detect


import openai
import dotenv
import os

dotenv.load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

system_prompt = """
"""

prompt = """
あなたは文書を校正するアシスタントです。
意味を変えない前提で、与えられた文章を訂正して出力してください。
英語で書かれている単語をそのまましてください。
修正のポイントは以下です。
1. 誤字脱字
2. 文法の誤り
3. 不自然な表現

例1:
===訂正前の文章開始===
昨日は10時に寝った。
「風邪は治った？」「はい、もう元気から大丈夫です」
===訂正前の文章終了===
訂正後の文章:
昨日は10時に寝た。
「風邪は治った？」「はい、もう元気だから大丈夫です」

例2:
===訂正前の文章開始===
きのうはは寒かったでしたす
今日は暑いでひょう
===訂正前の文章終了===
訂正後の文章:
昨日は寒かったです
今日は暑いです

以下の文章を訂正してください。
===訂正前の文章開始===
{passage}
===訂正前の文章終了===
訂正後の文章:"""


english_prompt = """
You are an assistant tasked with proofreading documents.
Under the premise of not changing the meaning, correct the provided text and output the revision.
Please keep any words written in a language other than English as they are.
The key points for revision are as follows:

Spelling and typing errors
Grammatical errors
Unnatural expressions
Example 1:
===Before Correction===
I goes to bed at 10 o'clock yesterday.
"Did you cold get better?" "Yes, I am fine because I already healthy."
===After Correction===
I went to bed at 10 o'clock yesterday.
"Did your cold get better?" "Yes, I'm fine because I'm already healthy."

Example 2:
===Before Correction===
Yesterday was very colding.
Today is very hoting.
===After Correction===
Yesterday was very cold.
Today is very hot.

Please correct the following text.
===Before Correction===
{passage}
===After Correction==="""


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
    st.title("文章校正アシスタント")
    st.write("文章を入力すると、文法や誤字脱字を修正してくれます。")
    st.write("日本語と英語をサポートしています。自動的に言語を判定します。")
    st.markdown("blog: <http://www.jiang.jp/posts/20230518_grammar_checker/>")
    option = st.selectbox(
        '使うモデルを選択してください',
        ("gpt-3.5-turbo", 'gpt-4')
    )
    orig_txt = st.text_area("Input Text", height=200)
    fixed_txt = ""
    if orig_txt:
        lang = detect(orig_txt)
        if lang == "ja":
            selected_prompt = prompt
        elif lang == "en":
            selected_prompt = english_prompt
        else:
            st.write("日本語か英語を入力してください")
            st.stop()
        
        output = openai.ChatCompletion.create(
        model=option,
        messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": selected_prompt.format(passage=orig_txt)},
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