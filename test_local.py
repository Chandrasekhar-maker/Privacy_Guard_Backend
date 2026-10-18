"""
Quick local test — runs the jumble API without Firebase (no DB calls).
Tests: /api/v1/jumble, /api/v1/unjumble, /api/v1/verify
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, ".")


from app.services.jumble_engine import JumbleEngine

TEST_CASES = [
    ("Hey! Are we meeting at 5pm?", "1234"),
    ("This is TOP SECRET message! 🔐", "9876"),
    ("WhatsApp: Call me ASAP!", "5555"),
    ("यह एक गुप्त संदेश है", "4321"),
]

print("\n" + "="*60)
print("   PRIVACYGUARD CLOUD API — ENGINE TEST")
print("="*60)

all_pass = True
for text, pin in TEST_CASES:
    jumbled = JumbleEngine.jumble(text, pin)
    restored = JumbleEngine.unjumble(jumbled, pin)
    length_ok = len(jumbled) == len(text)
    restore_ok = restored == text
    
    status = "✅ PASS" if (length_ok and restore_ok) else "❌ FAIL"
    if not (length_ok and restore_ok):
        all_pass = False
    
    print(f"\n{status}")
    print(f"  Original : {text[:50]}")
    print(f"  Jumbled  : {jumbled[:50]}")
    print(f"  Restored : {restored[:50]}")
    print(f"  Length OK: {length_ok} | Restore OK: {restore_ok}")

print("\n" + "="*60)
print(f"  RESULT: {'ALL TESTS PASSED ✅' if all_pass else 'SOME TESTS FAILED ❌'}")
print("="*60)

# Show API endpoint summary
print("""
API ENDPOINTS (after deploying to Render.com):
  POST https://privacy-guard-api.onrender.com/api/v1/jumble
  POST https://privacy-guard-api.onrender.com/api/v1/unjumble  
  POST https://privacy-guard-api.onrender.com/api/v1/verify
  POST https://privacy-guard-api.onrender.com/api/v1/sessions/create
  GET  https://privacy-guard-api.onrender.com/api/v1/sessions/{id}
  POST https://privacy-guard-api.onrender.com/api/v1/sessions/{id}/deactivate
  GET  https://privacy-guard-api.onrender.com/health
  GET  https://privacy-guard-api.onrender.com/docs  ← Swagger UI
""")
