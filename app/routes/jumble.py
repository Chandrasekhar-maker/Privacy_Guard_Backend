from fastapi import APIRouter, HTTPException
from ..models.schemas import JumbleRequest, JumbleResponse, UnjumbleRequest, UnjumbleResponse
from ..services.jumble_engine import JumbleEngine

router = APIRouter(prefix="/api/v1", tags=["Jumble"])


@router.post("/jumble", response_model=JumbleResponse, summary="Scramble text using PIN")
async def jumble_text(req: JumbleRequest):
    """
    Scramble any text (English, Hindi, Emojis, any language) using your PIN.
    
    - **Zero characters are added** — same length, same character set
    - **Deterministic** — same PIN + same text = same scramble every time
    - **Reversible** — only the correct PIN can restore it
    """
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty or whitespace only")

    try:
        result = JumbleEngine.jumble(req.text, req.pin)
        return JumbleResponse(
            success=True,
            original_length=len(req.text),
            result=result,
            result_length=len(result),
            characters_added=0,
            message=f"Text scrambled successfully ({len(result)} characters)",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Jumble failed: {str(e)}")


@router.post("/unjumble", response_model=UnjumbleResponse, summary="Restore scrambled text using PIN")
async def unjumble_text(req: UnjumbleRequest):
    """
    Restore scrambled text to its original form using the security PIN.
    
    - If the wrong PIN is provided, the output will be incorrect (different garbage)
    - No error is thrown for wrong PIN — the algorithm always produces output
    """
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Scrambled text cannot be empty")

    try:
        result = JumbleEngine.unjumble(req.text, req.pin)
        return UnjumbleResponse(
            success=True,
            result=result,
            message="Text restored successfully",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unjumble failed: {str(e)}")


@router.post("/verify", summary="Self-test the jumble algorithm")
async def verify_algorithm(req: JumbleRequest):
    """
    Verify that a text can be perfectly jumbled and restored with the given PIN.
    Returns True only if the algorithm is working correctly for this text+PIN pair.
    """
    try:
        is_valid = JumbleEngine.verify(req.text, req.pin)
        jumbled = JumbleEngine.jumble(req.text, req.pin)
        return {
            "success": True,
            "verified": is_valid,
            "original": req.text,
            "scrambled": jumbled,
            "original_length": len(req.text),
            "scrambled_length": len(jumbled),
            "characters_added": len(jumbled) - len(req.text),
            "message": "✅ Algorithm verified — zero characters added, fully reversible" if is_valid else "❌ Verification failed",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
