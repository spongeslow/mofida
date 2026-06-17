from affinitree import rubric


class FakeClient:
    """Returns a scripted sequence of scores, ignoring the prompt."""

    def __init__(self, scores):
        self.scores = list(scores)
        self.calls = 0

    def generate_json(self, prompt, *, seed):
        s = self.scores[self.calls]
        self.calls += 1
        return {"score": s, "evidence_quote": f"q{s}", "reasoning": f"r{s}"}


def test_agreeing_runs_no_third_call():
    client = FakeClient([3, 3])
    r = rubric.score_field("some value proposition", "offer.value_prop_text", client)
    assert r["score"] == 3
    assert client.calls == 2  # no third run when scores agree


def test_divergent_runs_trigger_third_and_median():
    client = FakeClient([1, 4, 4])  # |1-4| > 1 -> third run, median([1,4,4]) = 4
    r = rubric.score_field("x", "offer.value_prop_text", client)
    assert client.calls == 3
    assert r["score"] == 4


def test_score_is_clamped():
    client = FakeClient([9, 9])
    r = rubric.score_field("x", "offer.value_prop_text", client)
    assert r["score"] == 4  # clamped to rubric max


def test_empty_text_scores_zero_without_calls():
    client = FakeClient([])
    r = rubric.score_field("   ", "offer.value_prop_text", client)
    assert r["score"] == 0
    assert client.calls == 0


def test_score_profile_writes_back():
    from affinitree import StartupProfile

    profile = StartupProfile(offer={"value_prop_text": "clear value"})
    client = FakeClient([2, 2])
    out = rubric.score_profile_text_fields(profile, client)
    assert out["offer.value_prop_text"] == 2
    assert profile.rubric_scores["offer.value_prop_text"] == 2
