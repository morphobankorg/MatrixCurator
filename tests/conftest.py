import pytest

@pytest.fixture
def sample_nexus():
    return """#NEXUS
BEGIN TAXA;
    DIMENSIONS NTAX=3;
    TAXLABELS
        Taxon_A
        Taxon_B
        Taxon_C
    ;
END;

BEGIN CHARACTERS;
    DIMENSIONS NCHAR=2;
    FORMAT DATATYPE=STANDARD MISSING=? GAP=- SYMBOLS="0 1";
    MATRIX
    Taxon_A 00
    Taxon_B 11
    Taxon_C 01
    ;
END;
"""
