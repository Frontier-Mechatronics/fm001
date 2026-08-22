/* FM001 — project-owned reset handler.
 *
 * Step 4: introduce Reset_Handler as a symbol.
 *
 * There is still no vector table, so nothing points the core at this function. It is
 * currently unreachable code that exists to be compiled, linked and inspected. Its
 * eventual purpose is to be the target of word 1 of the vector table and to hand control
 * to main() once the C runtime environment is ready.
 *
 * The trap loop after main() is not decoration. PM0215 Rev 2 page 7/72: "On reset, the
 * processor loads the LR value 0xFFFFFFFF." Reset_Handler is entered by the reset
 * sequence, not by a call, so there is no valid return address in LR. Falling off the end
 * of this function would branch to 0xFFFFFFFF and fault. If main() ever returns, stopping
 * here is the defined behaviour we choose.
 */

extern int main(void);

void Reset_Handler(void)
{
    main();

    for (;;) {
    }
}
