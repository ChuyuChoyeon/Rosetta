try:
    import magic

    print(f"magic module: {magic}")
    print(f"dir(magic): {dir(magic)}")
    if hasattr(magic, "from_buffer"):
        print("magic.from_buffer exists")
    else:
        print("magic.from_buffer DOES NOT exist")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
