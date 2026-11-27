"""Run judge_correct_v2.py unchanged, but with only the math SDPA kernel (needed on Turing cards in s02; same model,
dtype, prompt, decoding). usage: python run_judge_mathsdp.py <judge_input> <out>"""
import sys, runpy, torch
torch.backends.cuda.enable_flash_sdp(False); torch.backends.cuda.enable_mem_efficient_sdp(False)
sys.argv = ["judge_correct_v2.py"] + sys.argv[1:]
runpy.run_path(sys.argv[0] if False else "scripts/judge_correct_v2.py", run_name="__main__")
