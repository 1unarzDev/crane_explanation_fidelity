# Grounded numeric presentation checks

Development utility only; no endpoint tolerance or no-motion threshold is frozen.

For a separately grounded odometry-distance proposition, decimal presentation is deterministically checked using its expressed decimal quantum: ordinary presentation may differ from the visible numerical reference by at most half that quantum. A literal exact assertion requires equality. A clearly rounded `0.000 m` can represent tiny nonzero drift, while “exactly zero” cannot. Neither licenses physical immobility, goal attainment, map-frame progress or extrapolation outside the visible sample window. Closed interval boundaries allow ordinary tie-rounding conventions without choosing one from results.

The check does not find claims in raw answers or establish their quantity, frame, window or scope. It does not decide required useful coverage: an excessively coarse but mathematically compatible number can still fail a final substantive-information rule. Semantic grounding, allowable useful precision/upper-bound language and complete claim extraction must be qualified separately. The helper is not automatically connected to primary labels and does not override retained judge judgments.

Tests cover ordinary rounding, scientific notation, wrong magnitude, literal exact-zero overclaims, unavailable/invalid references and bounded decimal parsing. No method outputs, human labels, alpha or episode outcomes are inputs.
