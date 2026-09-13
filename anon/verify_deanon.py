from core.processors.deanon import Deanon

mapping = {
    "[Person_1]": {"original": "Иван Петров", "category": "PERSON", "files": ["a.txt"]},
    "[Org_1]": {"original": "ООО Ромашка", "category": "ORG", "files": ["a.txt"]},
}
text = "Привет [Person_1], компания [Org_1] приглашает вас."
reverse = Deanon().load_map_from_data(mapping)
print(Deanon().deanon_text(text, reverse))
