import sys
try:
    import google.adk.planners
    print("Attributes of google.adk.planners:")
    print(dir(google.adk.planners))
except Exception as e:
    print(f"Error: {e}")

try:
    import google.adk
    print("\nAttributes of google.adk:")
    print(dir(google.adk))
except Exception as e:
    print(f"Error: {e}")
