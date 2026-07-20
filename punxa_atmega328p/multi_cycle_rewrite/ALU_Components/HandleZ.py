import py4hw

class HandleZ(py4hw.Logic):
    """
    STUB -- the real behavioral (non-STRUC) 'HandleZ' component was not
    provided to this test sandbox. It is NOT instantiated by ALU_STRUC
    (the structural ALU actually used by Datapath/MulticycleProcessor);
    it exists only because ALU.py unconditionally imports the whole
    ALU_Components package at module load time (used by the dead/unused
    behavioral 'ALU' class). If this stub is ever actually instantiated,
    that means something unexpectedly took the behavioral path, so it
    fails loudly instead of silently producing wrong results.
    """
    def __init__(self, *args, **kwargs):
        raise NotImplementedError(
            "HandleZ (behavioral ALU_Components version) is a test stub "
            "and was not expected to be instantiated -- only ALU_STRUC "
            "should be used by this rewrite."
        )
