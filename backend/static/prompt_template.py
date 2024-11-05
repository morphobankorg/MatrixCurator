generative_prompt="""Here is a sample of text from a phylogenetic research paper. Please extract the character descriptions and their corresponding states for characters between character number {start} and character number {end}, including all the characters in between, as an XML tree. The XML tree should be formatted according to the following schema:

<characters>
	<character index=" " name="character name">
		<state value="0">state description</state>
		<state value="1">state description</state>
	</character>
</characters>

EXAMPLE:

input: 
Length of paddle (VI-7-9)/width of paddle: 0=>3.2; 1 = <2.76. ADELOPHTHALMOID PHYLOGENY AND PALAEOECOLOGY.
Pallial line in left and right valves sinuous (Fig. 3.12, arrow 62-0) 0 straight (Fig. 1.12, arrow 62-1) 1.
Anterior palatal vacuity rounded (0), heart-, kidney- (1) or butterfly- shaped (2).
Lamina palatina visible (1) or not (0) on the premaxilla.
5. PREMAX 7. Premaxillae more (0) or less than (1)
two-thirds as wide as skull table.
Ectopterygoid tusks present (0) or not (1).
Chondrophore projects (left valve) slightly past valve edge posterior of chondrophore, but is ﬂush with valve edge anterior of socket (Fig. 2.16) 0 beyond commissure (Fig. 3.7, arrow 41-1) 1.
8. TRU VER 29. Intravertebral foramina for spinal
nerves in at least some trunk vertebrae: absent (0);
present (1). 
9. SPTMAX 2. Septomaxilla a detached ossification inside nostril: no (0); yes (1).

output: 
<characters>
    <character index="1" name="Length of paddle (VI-7-9)/width of paddle">
        <state value="0">>3.2</state>
        <state value="1"><2.76</state>
    </character>
    <character index="2" name="Pallial line in left and right valves">
        <state value="0">sinuous</state>
        <state value="1">straight</state>
    </character>
    <character index="3" name="Anterior palatal vacuity shape">
        <state value="0">rounded</state>
        <state value="1">heart-, kidney-</state>
        <state value="2">butterfly-shaped</state>
    </character>
    <character index="4" name="Lamina palatina visible on the premaxilla">
        <state value="0">Not visible</state>
        <state value="1">Visible</state>
    </character>
     character index="5" name="PREMAX 7. Premaxillae">
        <state value="0">more than two-thirds as wide as skull table</state>
        <state value="1">less than two-thirds as wide as skull table</state>
    </character>
    <character index="6" name="Ectopterygoid tusks present">
        <state value="0">Present</state>
        <state value="1">Not present</state>
    </character>
    <character index="7" name="Chondrophore projects (left valve)">
        <state value="0">slightly past valve edge posterior of chondrophore, but is flush with valve edge anterior of socket</state>
        <state value="1">beyond commissure</state>
    </character>
    <character index="8" name="TRU VER 29. Intravertebral foramina for spinal
nerves in at least some trunk vertebrae">
        <state value="0">absent</state>
        <state value="1">present</state>
    </character>
    <character index="9" name="SPTMAX 2. Septomaxilla a detached ossification inside nostril">
        <state value="0">no</state>
        <state value="1">yes</state>
    </character>

</characters>

Please ignore the publication details & all the citations when extracting.

"""