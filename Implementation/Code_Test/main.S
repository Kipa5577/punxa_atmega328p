    #include <avr/io.h>         

    .global main 		
    
    
    main:
    ldi r16, 0x01
    out  _SFR_IO_ADDR(DDRB), r16
    out _SFR_IO_ADDR(PORTB), r16
    
    loop:
    ;; delay loop
    ldi  r18, 6
    ldi  r19, 19	
    ldi  r20, 174
    L1:
    dec  r20
    brne L1
    dec  r19
    brne L1
    dec  r18
    brne L1	
    
    in r16, _SFR_IO_ADDR(PORTB)
    com r16
    out _SFR_IO_ADDR(PORTB), r16
    
    rjmp loop