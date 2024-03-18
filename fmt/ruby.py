from fmt.session import kks
from Levenshtein import opcodes
from share.assets import ruby_pattern, ruby_content_pattern


def result_to_index(result: dict) -> tuple[str, list[tuple[float, str]]]:
    # {'orig': '古い', 'hira': 'ふるい', 'kana': 'フルイ', 'hepburn': 'furui', 'kunrei': 'furui', 'passport': 'furui'}
    output = ''
    rubies = []
    orig = result['orig']
    hira = result['hira']

    ops = opcodes(orig, hira)
    temp_hira = ''
    for op in ops:
        orig_start, orig_end = op[1], op[2]
        hira_start, hira_end = op[3], op[4]
        if op[0] == 'insert':
            temp_hira += hira[hira_start:hira_end]
        elif op[0] == 'replace':
            temp_hira += hira[hira_start:hira_end]
            orig_index_center = orig_start + (orig_end - 1 - orig_start) / 2
            rubies.append((orig_index_center, temp_hira))
            temp_hira = ''
            output += orig[orig_start:orig_end]
        else:
            output += orig[orig_start:orig_end]
    return output, rubies


def get_ruby_index(text: str) -> tuple[str, list[tuple[float, str]]]:
    result = kks.convert(text)
    output = ''
    rubies = []
    for item in result:
        if item['orig'] == item['hira'] or item['orig'] == item['kana']:
            output += item['orig']
        else:
            o, r = result_to_index(item)
            index = len(output)
            output += o
            rubies.extend([(index + i, r) for i, r in r])

    return output, rubies


def result_to_pair(result: dict) -> list[list[str, str]]:
    # input: {'orig': '古い', 'hira': 'ふるい'}
    # output: [['古', 'ふる'], ['い', '']]

    orig = result['orig']
    hira = result['hira']
    ops = opcodes(orig, hira)

    output = []
    temp_hira = ''
    for op in ops:
        orig_start, orig_end = op[1], op[2]
        hira_start, hira_end = op[3], op[4]
        if op[0] == 'insert':
            temp_hira += hira[hira_start:hira_end]
        elif op[0] == 'replace':
            temp_hira += hira[hira_start:hira_end]
            output.append([orig[orig_start:orig_end], temp_hira])
            temp_hira = ''
        else:
            output.append([orig[orig_start:orig_end], ''])

    return output


def get_ruby_pair(text: str) -> list[list[str, str]]:
    result = kks.convert(text)
    output = []
    for item in result:
        if item['orig'] == item['hira'] or item['orig'] == item['kana']:
            output.append([item['orig'], ''])
        else:
            output.extend(result_to_pair(item))
    return output


def magic_ruby_to_index(text: str) -> tuple[str, list[tuple[int, str]]]:
    """
    测{RUBY#[D]示例}试
    """
    ruby_text = ruby_pattern.findall(text)
    if not ruby_text:
        return text, []

    rubies = []
    output = ''
    last_ruby_end = 0
    for ruby in ruby_text:
        content = ruby_content_pattern.findall(ruby)[0]
        original_index = text.index(ruby)
        if last_ruby_end:
            output += text[last_ruby_end:original_index]
        else:
            output += text[:original_index]
        rubies.append((len(output) - 1, content))
        last_ruby_end = original_index + len(ruby)

    output += text[last_ruby_end:]
    return output, rubies


def magic_ruby_to_pair(text: str) -> list[list[str, str]]:
    """
    input: 测{RUBY#[D]示例}试
    output: [['测', '示例'], ['试', '']]
    """
    ruby_text = ruby_pattern.findall(text)
    if not ruby_text:
        return [[text, '']]

    output = []
    last_ruby_end = 0
    for ruby in ruby_text:
        content = ruby_content_pattern.findall(ruby)[0]
        original_index = text.index(ruby)
        # based_char_index = original_index - 1
        # in every loop
        # add text before ruby
        text_before_ruby = text[last_ruby_end:original_index - 1]
        if text_before_ruby:
            output.append([text_before_ruby, ''])
        # add ruby
        output.append([text[original_index - 1], content])
        last_ruby_end = original_index + len(ruby)

    if last_ruby_end < len(text):
        output.append([text[last_ruby_end:], ''])

    return output
