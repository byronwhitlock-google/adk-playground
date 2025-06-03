import asyncio
import io
import sys
from dotenv import load_dotenv

# Import functions from other test files
from chirp_test import run_chirp_text_to_speech_example
# For music_test, importing the module will execute its content
# We will capture its output during the import process.
# import music_test 
from mux_music_test import run_mux_music_test
from mux_test import run_mux_audio_test
from speech_test import run_sync_explicit_example
from tool_test import main as run_tool_test_main  # Renaming to avoid potential conflicts
from video_generation_test import run_video_generation_example
from video_length_test import run_get_video_length_test

ERROR_KEYWORDS = ["ERROR", "FAILED", "Traceback"]

def check_output_for_errors(output_text):
    """Checks if the output text contains any error keywords."""
    output_lower = output_text.lower()
    for keyword in ERROR_KEYWORDS:
        if keyword.lower() in output_lower:
            return True
    return False

async def main():
    load_dotenv()  # Load environment variables from .env file
    results = []
    original_stdout = sys.stdout

    # Test 1: chirp_test
    test_name = "chirp_test"
    print(f"Starting {test_name}...")
    captured_output = io.StringIO()
    sys.stdout = captured_output
    try:
        run_chirp_text_to_speech_example()
    except Exception as e:
        print(f"--- {test_name} EXCEPTION ---")
        print(str(e)) # Ensure exception is captured
    finally:
        sys.stdout = original_stdout
        output_content = captured_output.getvalue()
        status = "FAILED" if check_output_for_errors(output_content) else "PASSED"
        results.append((test_name, status, output_content))
        print(f"{test_name} finished. Status: {status}\n")

    # Test 2: music_test (executed on import)
    test_name = "music_test"
    print(f"Starting {test_name} (runs on import)...")
    captured_output = io.StringIO()
    sys.stdout = captured_output
    try:
        # Importing the module executes its code
        import music_test 
    except Exception as e:
        print(f"--- {test_name} EXCEPTION ---")
        print(str(e))
    finally:
        sys.stdout = original_stdout
        output_content = captured_output.getvalue()
        # music_test prints "Music generation or upload failed" on error.
        status = "FAILED" if check_output_for_errors(output_content) or "generation or upload failed" in output_content.lower() else "PASSED"
        results.append((test_name, status, output_content))
        print(f"{test_name} finished. Status: {status}\n")

    # Test 3: mux_music_test
    test_name = "mux_music_test"
    print(f"Starting {test_name}...")
    captured_output = io.StringIO()
    sys.stdout = captured_output
    try:
        await run_mux_music_test()
    except Exception as e:
        print(f"--- {test_name} EXCEPTION ---")
        print(str(e))
    finally:
        sys.stdout = original_stdout
        output_content = captured_output.getvalue()
        status = "FAILED" if check_output_for_errors(output_content) else "PASSED"
        results.append((test_name, status, output_content))
        print(f"{test_name} finished. Status: {status}\n")

    # Test 4: mux_test (run_mux_audio_test)
    test_name = "mux_test (run_mux_audio_test)"
    print(f"Starting {test_name}...")
    captured_output = io.StringIO()
    sys.stdout = captured_output
    try:
        await run_mux_audio_test()
    except Exception as e:
        print(f"--- {test_name} EXCEPTION ---")
        print(str(e))
    finally:
        sys.stdout = original_stdout
        output_content = captured_output.getvalue()
        status = "FAILED" if check_output_for_errors(output_content) else "PASSED"
        results.append((test_name, status, output_content))
        print(f"{test_name} finished. Status: {status}\n")

    # Test 5: speech_test (run_sync_explicit_example)
    test_name = "speech_test (run_sync_explicit_example)"
    print(f"Starting {test_name}...")
    captured_output = io.StringIO()
    sys.stdout = captured_output
    try:
        run_sync_explicit_example()
    except Exception as e:
        print(f"--- {test_name} EXCEPTION ---")
        print(str(e))
    finally:
        sys.stdout = original_stdout
        output_content = captured_output.getvalue()
        status = "FAILED" if check_output_for_errors(output_content) else "PASSED"
        results.append((test_name, status, output_content))
        print(f"{test_name} finished. Status: {status}\n")

    # Test 6: tool_test (video_join_tool test)
    test_name = "tool_test (video_join_tool test)"
    print(f"Starting {test_name}...")
    captured_output = io.StringIO()
    sys.stdout = captured_output
    try:
        await run_tool_test_main()
    except Exception as e:
        print(f"--- {test_name} EXCEPTION ---")
        print(str(e))
    finally:
        sys.stdout = original_stdout
        output_content = captured_output.getvalue()
        status = "FAILED" if check_output_for_errors(output_content) else "PASSED"
        results.append((test_name, status, output_content))
        print(f"{test_name} finished. Status: {status}\n")

    # Test 7: video_generation_test
    test_name = "video_generation_test"
    print(f"Starting {test_name}...")
    captured_output = io.StringIO()
    sys.stdout = captured_output
    try:
        await run_video_generation_example()
    except Exception as e:
        print(f"--- {test_name} EXCEPTION ---")
        print(str(e))
    finally:
        sys.stdout = original_stdout
        output_content = captured_output.getvalue()
        status = "FAILED" if check_output_for_errors(output_content) else "PASSED"
        results.append((test_name, status, output_content))
        print(f"{test_name} finished. Status: {status}\n")

    # Test 8: video_length_test
    test_name = "video_length_test"
    print(f"Starting {test_name}...")
    captured_output = io.StringIO()
    sys.stdout = captured_output
    try:
        await run_get_video_length_test()
    except Exception as e:
        print(f"--- {test_name} EXCEPTION ---")
        print(str(e))
    finally:
        sys.stdout = original_stdout
        output_content = captured_output.getvalue()
        status = "FAILED" if check_output_for_errors(output_content) else "PASSED"
        results.append((test_name, status, output_content))
        print(f"{test_name} finished. Status: {status}\n")

    print("\n\n--- Test Execution Summary ---")
    total_tests = len(results)
    passed_tests = sum(1 for _, status, _ in results if status == "PASSED")
    failed_tests = total_tests - passed_tests

    print(f"Total tests run: {total_tests}")
    print(f"Tests PASSED: {passed_tests}")
    print(f"Tests FAILED: {failed_tests}")

    if failed_tests > 0:
        print("\n--- Failed Tests ---")
        for name, status, output in results:
            if status == "FAILED":
                print(f"- {name}")
                # Optionally, print the detailed output for failed tests again, or a snippet
                # For now, just listing names as requested.
                # print("--- Output ---")
                # print(output) # This can be very verbose, consider if needed here.
                # print("--------------")
        print("--------------------")

    print("\n--- Detailed Test Results ---")
    for name, status, output in results:
        print(f"\nTest: {name}")
        print(f"Status: {status}")
        if status == "FAILED":
            print("--- Output ---")
            print(output) # Keep detailed output for failed tests here
            print("--------------")
    
    print("\n--- End of Test Run ---")


if __name__ == "__main__":
    asyncio.run(main())
