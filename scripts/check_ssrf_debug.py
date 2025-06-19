from src.backend.services.intelligent_analyzer import IntelligentCodeAnalyzer

TEST_CODE = '''
import requests

def test_func(url):
    requests.get(url)
'''

def main():
    analyzer = IntelligentCodeAnalyzer()
    issues = analyzer.analyze_semantics("test_ssrf.py", TEST_CODE, "python")
    print("\n[RESULT] Issues detected:")
    for issue in issues:
        print(f"- {issue.issue_type}: {issue.description} (line {issue.line_number})")

if __name__ == "__main__":
    main() 