uv run pytest \
  tests/test_prompt_builder.py \
  tests/test_reference_builder.py \
  tests/test_ocr_cache.py \
  tests/test_vision_parser.py \
  tests/test_generation_prompt_flow.py -v


uv run pytest tests/test_tutor_prompt_builder.py tests/test_lesson_plan_builder.py -v
