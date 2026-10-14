# Milestone F130: Coucou's board shows a stale building card

> **State:** idea · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-10-14.

## Notes
From the terminal session of 2026-10-14 that built ADR 30 (sessions B, C, D).

After the split, Coucou's board shows one card as "building" (the Projects page says "1
building") though all of Coucou's milestones, m0 to m4, are done. It's a state from before the
split: the database rows moved by rule (milestones not `m<N>` to Softfield) and Coucou kept its
own, including that stale state.

Find which card it is (`milestones` where project is coucou and state is building), set it from
its card doc, and check nothing else carried over wrong (Coucou's 33 tickets and 41 runs, its
owner items).
