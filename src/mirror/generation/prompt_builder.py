#TODO: prompt can be global var passed around, this can be improved
def build_exercise_prompt(learner_name: str, topic: str, reference_excerpt: str) -> str:
    return f"""
            You are an expert language tutor.
            
            Create a new language exercise for the learner named {learner_name}.
            
            Requirements:
            - The new exercise topic must be: {topic}
            - Use the reference worksheet only as a guide for tone, structure, difficulty, and exercise style
            - Do not copy the worksheet verbatim
            - Produce a clean teacher-ready exercise
            - Keep the format simple and readable
            - Include clear instructions
            - Include 5 to 8 questions
            
            Reference worksheet excerpt:
            {reference_excerpt}
            """.strip()
