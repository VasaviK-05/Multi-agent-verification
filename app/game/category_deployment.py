"""Explicit owned adapter for the existing orchestrator runtime type boundary.

This factory is never called by create_game_runtime/settings. It constructs no
models, changes no default and does not mutate the supplied historical runtime.
"""


def create_category_game_runtime(legacy_runtime, category_runtime, *, allow_synthetic_for_tests=False):
    from app.game.category_runtime import CategoryGameRuntime
    from app.game.deployment import FlexiblePolicyGameRuntime

    if not isinstance(legacy_runtime, FlexiblePolicyGameRuntime):
        raise TypeError('category composition requires the owned bounded flexible runtime')
    if not isinstance(category_runtime, CategoryGameRuntime):
        raise TypeError('category composition requires reviewed category runtime construction')
    if type(allow_synthetic_for_tests) is not bool:
        raise TypeError('test-only permission must be an explicit boolean')
    if category_runtime._allow_synthetic_for_tests and not allow_synthetic_for_tests:
        raise ValueError('synthetic category runtime cannot enter deployment')
    dispatcher = CategoryGameRuntime.compose(legacy_runtime, category_runtime)

    class OptInCategoryGameRuntime(FlexiblePolicyGameRuntime):
        """Accepted by the unchanged orchestrator's configured-runtime guard."""
        def __init__(self):
            # Preserve the legacy instance itself; do not reconstruct its RNG,
            # factories, registry, relocation settings or provenance observer.
            self._configuration = legacy_runtime._configuration
            self._dispatcher = dispatcher

        def run(self, selector, analysis, request, validation_id, *, execution_journal=None):
            return self._dispatcher.run(selector, analysis, request, validation_id, execution_journal=execution_journal)

    return OptInCategoryGameRuntime()
