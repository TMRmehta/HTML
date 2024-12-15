import re

exclude = """
google-cloud-aiplatform
google-cloud-bigquery
google-crc32c
google-resumable-media
googleapis-common-protos
langgraph-studio
langserve
langsmith
requests
regex
tqdm
unstructured
unstructured-client
""".strip().split('\n')

with open("requirements.txt", "r") as f:
    data = f.read()

for item in exclude:
    # match the whole line: package==version
    pattern = rf'^{item}==[^\n]+'
    match = re.findall(pattern, data, flags=re.MULTILINE)
    if match:
        for m in match:
            data = re.sub(re.escape(m), f"# {m}", data)
        print(f"Removed {item}")

with open("requirements.txt", "w") as f:
    f.write(data)
