# Introduce
我的本科毕设
# Get Start
1. 项目依赖以下库运行：  
- pandas  
- stramlit 
- openai
- langchain  
- pydeck 
- millify  
运行项目前，请确保所有需要的模块都已经安装。在命令行中输入
```shell
pip3 install model_name 
```
2. 在项目目录下创建文件夹`.streamlit` ,并在此文件夹内创建toml文件`secrets.toml`,并在文件内输入
```toml
OPENAI_API_KEY = ''
HF_API_KEY = ''
```
`OPENAI_API_KE`是chatgpt的API key，`HF_API_KEY`是Hugging Face的API key，你需要自己提供这两个key。  
3. 在项目路径下的终端输入
```shell
streamlit run home.py
```
即可运行项目。
