"""Unit tests for the dependency resolution engine.

The worked example from new-logic.md §5.5 is the primary fixture.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.dependency import affected_axes, dependents_of, DEPENDS_ON


# ---------------------------------------------------------------------------
# Graph structure sanity
# ---------------------------------------------------------------------------

def test_all_deps_are_known_axes():
    known = set(DEPENDS_ON.keys())
    for axis, deps in DEPENDS_ON.items():
        for dep in deps:
            assert dep in known, f"{axis} depends on unknown axis '{dep}'"


def test_roadmap_has_no_explicit_deps():
    assert DEPENDS_ON["roadmap"] == []


# ---------------------------------------------------------------------------
# dependents_of
# ---------------------------------------------------------------------------

def test_ideation_dependents():
    deps = dependents_of("ideation")
    # market, product, brand, legal all depend on ideation
    assert {"market", "product", "brand", "legal"}.issubset(deps)


def test_roadmap_has_no_dependents():
    # roadmap is a sink — nothing depends on it
    assert dependents_of("roadmap") == set()


# ---------------------------------------------------------------------------
# affected_axes — doc's §5.5 worked example (must match exactly)
# ---------------------------------------------------------------------------

def test_business_model_change():
    """new-logic.md §5.5 example: editing the pricing model."""
    result = affected_axes({"business-model"})
    # roadmap is always last
    assert result[-1] == "roadmap"
    body = result[:-1]
    # These four must be re-run (in some valid topo order)
    assert set(body) == {"operations", "legal", "marketing", "sales"}
    # ideation, market, product, brand must NOT appear
    for untouched in ("ideation", "market", "product", "brand"):
        assert untouched not in result


def test_business_model_operations_order():
    """SCC pair: business-model always before operations in the output."""
    result = affected_axes({"business-model"})
    body = result[:-1]
    if "business-model" in body and "operations" in body:
        assert body.index("business-model") < body.index("operations")


def test_ideation_change_propagates_widely():
    """Editing ideation affects almost everything downstream."""
    result = affected_axes({"ideation"})
    assert result[-1] == "roadmap"
    body = set(result[:-1])
    # market, product, brand, legal, and transitively everything, should be dirty
    assert {"market", "product", "brand", "legal"}.issubset(body)


def test_no_change_returns_empty():
    assert affected_axes(set()) == []


def test_leaf_change_only_roadmap():
    """sales has no dependents except roadmap."""
    result = affected_axes({"sales"})
    assert result == ["roadmap"]


def test_operations_change_includes_scc_partner():
    """Changing operations must pull in business-model (SCC) + its dependents."""
    result = affected_axes({"operations"})
    body = set(result[:-1])
    assert "business-model" in body
    assert "marketing" in body
    assert "sales" in body


def test_roadmap_always_last():
    for axis in ("ideation", "market", "product", "brand",
                 "business-model", "legal", "operations", "marketing", "sales"):
        result = affected_axes({axis})
        if result:
            assert result[-1] == "roadmap"


def test_multiple_changed_axes():
    result = affected_axes({"market", "brand"})
    assert result[-1] == "roadmap"
    # product depends on market; marketing depends on brand and product
    body = set(result[:-1])
    assert "product" in body
    assert "marketing" in body
