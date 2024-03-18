import re


replace_pattern = re.compile(r'\{.*?\}')
html_tag_pattern = re.compile(r'<.*?>')
ruby_pattern = re.compile(r'\{RUBY\#\[D\](.*?)\}')
ruby_content_pattern = re.compile(r'\{RUBY\#\[[DS]\](.*?)\}')
