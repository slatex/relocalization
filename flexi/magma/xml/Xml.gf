abstract Xml = MagmaFormula ** {
    cat
        Tag;
        Epsilon;  -- empty string

    fun
        epsilon : Epsilon;  -- empty string
        tag : Int -> Tag;
        wrap_math : Tag -> Epsilon -> Formula;   -- signature is hard-coded in gfxml.py!
}
