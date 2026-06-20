#include <stdio.h>
#include <stdint.h>

//VARIABLES
uint8_t r1,r2;
uint16_t result;
uint8_t opcode;
uint16_t high,low,adress,mod;


//OPCODES
#define load 0x01
#define add 0x02
#define sub 0x03
#define jmp 0x04
#define mul 0x05
#define push 0x06
#define pop 0x07
#define jz 0x08
#define jnz 0x09
#define jc 0x0A
#define jnc 0x0B
#define cmp 0x0C
#define je 0x0D
#define jl 0x0E
#define jg 0x0F
#define stop 0xFF

//MEMORY : CODE / STACK SEGMENT
uint8_t memory[65536]={0x01,0x01,0, //load r1,1
                       0x01,0x02,15,//load r2,15
                       0x03,0x82,0x01,//sub r2,[1]
                       0xFF};          //HALT



//GENERAL PURPOSE REGISTERS   R0-R3 //LOOP REGISTER LR(R4) //ARITHMETIC REGISTER AR(R5)                
uint8_t registers[6];  

//FLAG REGISTERS
int CF,ZF;

//RAM

uint8_t RAM[256]={7,10,255};

//PORGRAM COUNTER
uint16_t PC=0;

//STACK POINTER
uint16_t SP=65535;

//HELP FUNCTIONS
uint16_t jump(){
           high=memory[PC];
           PC++;
           low=memory[PC];
           return low | (high << 8);
           
}



int running=1;

void bug(){
    printf("BUG HAPPENED\n");
    running=0;

}



int main() {
    while(running==1){
       opcode=memory[PC];
       PC++;
       switch(opcode){
        case load:
            adress=memory[PC];
            mod = adress & 0xC0;
            mod = mod >> 6 ;
            r1= adress & 0x3F;
            PC++;
            switch(mod){
               case 0:
                    registers[r1]=memory[PC];
                    break;
                case 1:
                    r2=memory[PC];
                    registers[r1]=registers[r2];
                    break;
                case 2:
                    registers[r1]=RAM[memory[PC]];
                    break;
                case 3:
                    r2=memory[PC];
                    registers[r1]=RAM[registers[r2]];
                    break;
                default :
                    bug();
                    break;
            }
            PC++;
            break;
        case add:
            adress=memory[PC];
            mod = adress & 0xC0;
            mod = mod >> 6 ;
            r1= adress & 0x3F;
            PC++;
            switch(mod){
               case 0:
                   result=(uint16_t)memory[PC]+(uint16_t)registers[r1];
                   registers[r1]+=memory[PC];
                   break;
               case 1:
                   r2=memory[PC];
                   result=(uint16_t)registers[r1]+(uint16_t)registers[r2];
                   registers[r1]+=registers[r2];
                   break;
               case 2:
                  result=(uint16_t)registers[r1]+(uint16_t)RAM[memory[PC]];
                  registers[r1]+=RAM[memory[PC]];
                  break;
               case 3:
                  r2=memory[PC];
                  result=(uint16_t)registers[r1]+(uint16_t)RAM[registers[r2]];
                  registers[r1]+=RAM[registers[r2]];
                  break;
            }
          CF=(result>255) ? 1:0;
          ZF=(registers[r1]==0) ? 1:0;
          PC++;
                   
            

            
           break;

        case sub:
            adress=memory[PC];
            mod = adress & 0xC0;
            mod = mod >> 6 ;
            r1= adress & 0x3F;
            PC++;
            switch(mod){
               case 0:   
                  CF=(registers[r1]<memory[PC]) ? 1:0;     
                   registers[r1]-=memory[PC];
                   break;
               case 1:
                   r2=memory[PC];
                   CF=(registers[r1]<registers[r2]) ? 1:0;
                   registers[r1]-=registers[r2];
                   break;
               case 2:
                  CF=(registers[r1]<RAM[memory[PC]]) ? 1:0;
                  registers[r1]-=RAM[memory[PC]];
                  break;
               case 3:
                  r2=memory[PC];
                  CF=(registers[r1]<RAM[registers[r2]]) ? 1:0;
                  registers[r1]-=RAM[registers[r2]];
                  break;
            }
          
          ZF=(registers[r1]==0) ? 1:0;
          PC++;
            break;
            
        case jmp:
           PC=jump();
           break; 

        case mul:
           r1=memory[PC];
           PC++;
           result=registers[0]*registers[r1];
           registers[5]=(result>>8) & 0xFF;
           registers[0]=result & 0xFF;
           break;
        
        case push :
           SP--;
           r1=memory[PC];
           PC++;
           memory[SP]=registers[r1];
           if(SP<=PC){
            printf("STACK OVERFLOW\n");
            running=0;
            break;
           }
           break;

        case pop :
           if(SP>=65535){
            printf("STACK UNDERFLOW\n");
            running=0;
            break;
           }
           r1=memory[PC];
           PC++;
           registers[r1]=memory[SP];
           SP++;
           break;

        case jz:
           if(ZF==1){
           PC=jump();
            break;
           }
           else{
            PC+=2;
            break;
           }

        case jnz:
           if(ZF==0){
            PC=jump();
            break;
           }
           else{
            PC+=2;
            break;
           }
        case jc:
            if(CF==1){
           PC=jump();
            break;
           }
           else{
            PC+=2;
            break;
           }
           
        case jnc:
            if(CF==0){
            PC=jump();
            break;
           }
           else{
            PC+=2;
            break;
           }

        case cmp:
           r1=memory[PC];
           PC++;
           r2=memory[PC];
           PC++;
           if(registers[r1]==registers[r2]){CF=0;ZF=1;}
           else{if(registers[r1]>registers[r2]){
               CF=0;
               ZF=0;
           }
             else{
                CF=1;
                ZF=0;
             } }

           break;

        case je:
            if(ZF==1){
            PC=jump();
            break;
           }
           else{
            PC+=2;
            break;
           }

        case jl:
            if(CF==1){
            PC=jump();
            break;
           }
           else{
            PC+=2;
            break;
           }

        case jg:
             if(CF==0 && ZF==0){
            PC=jump();
            break;
           }
           else{
            PC+=2;
            break;
           }

        case stop:
           running=0;
           printf("RUNNED SUCCESFULLY\n");
           break;
        
        

        default:
          bug();
          break;
}
       
    }
    

   printf("%d",registers[2]);
    return 0;
}