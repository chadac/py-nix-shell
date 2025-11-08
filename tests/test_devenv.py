"""Tests for nix_shell.devenv module."""

from nix_shell import dsl
from nix_shell.build import NixShell
from nix_shell.dsl.filesystem import StorePath
from nix_shell.module import Module, ModuleExpr
from nix_shell.third_party.devenv import DevenvShell
from tests.helpers import assert_match_nix

sample_module = Module(
    params=[dsl.v("pkgs")],
    config=dsl.attrs(
        packages=[dsl.raw("pkgs.git")],
    ),
)

sample_module_2 = Module(
    params=[dsl.v("pkgs")],
    config=dsl.attrs(
        packages=[dsl.raw("pkgs.curl")],
    ),
)


def test_devenv_shell_creation(snapshot):
    """Test that DevenvShell can be created with required parameters."""
    shell = DevenvShell()

    assert_match_nix(snapshot, dsl.dumps(shell.expr), "devenv_shell_empty.nix")


def test_devenv_shell_with_modules():
    """Test DevenvShell with custom modules."""
    shell = DevenvShell(modules=[sample_module])

    assert len(shell.modules) == 1
    assert shell.modules[0] == sample_module


def test_devenv_shell_expression_generation(snapshot):
    """Test that DevenvShell generates valid Nix expressions."""
    shell = DevenvShell()

    expr = shell.expr
    expr_str = dsl.dumps(expr)

    assert_match_nix(snapshot, expr_str, "devenv_basic_shell.nix")


def test_devenv_shell_expression_with_modules(snapshot):
    """Test DevenvShell expression generation with custom modules."""
    shell = DevenvShell(
        modules=[sample_module],
    )

    expr_str = dsl.dumps(shell.expr)

    assert_match_nix(snapshot, expr_str, "devenv_shell_with_module.nix")


def test_devenv_shell_integration_with_nix_shell():
    """Test that DevenvShell expressions work with NixShell."""
    shell = DevenvShell()

    expr = shell.expr
    expr_str = dsl.dumps(expr)

    # Create a NixShell using the expression
    nix_shell = NixShell.create(expr=expr_str)

    # Verify NixShell was created successfully
    assert nix_shell is not None
    assert nix_shell.params["expr"] == expr_str

    # The expression should be valid enough that build_id can be computed
    assert len(nix_shell.build_id) > 0


def test_devenv_shell_module_expr_integration(snapshot):
    """Test DevenvShell with ModuleExpr."""
    module_expr = ModuleExpr(
        path=StorePath.from_string(dsl.dumps(sample_module.mod_expr))
    )

    shell = DevenvShell(
        modules=[module_expr],
    )

    expr = shell.expr
    expr_str = dsl.dumps(expr)

    assert_match_nix(snapshot, expr_str, "devenv_shell_with_module_expr.nix")

    # Should still be valid for NixShell
    nix_shell = NixShell.create(expr=expr_str)
    assert nix_shell is not None


def test_devenv_shell_multiple_modules(snapshot):
    """Test DevenvShell with multiple modules."""
    module1 = sample_module
    module2 = sample_module_2

    shell = DevenvShell(
        modules=[module1, module2],
    )

    expr = shell.expr
    expr_str = dsl.dumps(expr)

    assert_match_nix(snapshot, expr_str, "devenv_shell_with_multiple_modules.nix")

    # Should still be valid for NixShell
    nix_shell = NixShell.create(expr=expr_str)
    assert nix_shell is not None
    assert len(nix_shell.build_id) > 0
