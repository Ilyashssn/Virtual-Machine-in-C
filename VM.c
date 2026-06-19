#include <stdio.h>
#include <stdint.h>
uint8_t r1,r2;
uint16_t result;

//OPCODES
#define load 0x01
#define add 0x02
#define sub 0x03
#define jmp 0x04
#define mul 0x05
#define stop 0x0F

//MEMORY : CODE / STACK SEGMENT
uint8_t memory[65536]={0x01,0x00,0x0A, //load r0,10 0
                     0x01,0x01,0x03, //load r1,3   3
                     0x01,0x02,0x01,  //load r2,1  6
                     0x02,0x00,0x01, //add r0,r1   9
                     0x02,0x02,0x00, //add r2,r0   12
                     0x05,0x02,      //MUL r2
                     0x0F};          //HALT

//GENERAL PURPOSE REGISTERS   R0-R3 //LOOP REGISTER LR(R4) //ARITHMETIC REGISTER AR(R5)                
uint8_t registers[6];  

//PORGRAM COUNTER
int PC=0;

//STACK POINTER
int SP=65535;


uint8_t opcode;
int running=1;

int main() {
    while(running==1){
       opcode=memory[PC];
       PC++;
       switch(opcode){
        case load:
            opcode=memory[PC];
            PC++;
            registers[opcode]=memory[PC];
            PC++;
            break;
        case add:
            r1=memory[PC];
            PC++;
            r2=memory[PC];
            PC++;
            registers[r1]+=registers[r2];
           break;

        case sub:
            r1=memory[PC];
            PC++;
            r2=memory[PC];
            PC++;
            registers[r1]-=registers[r2];
            break;
            
        case jmp:
           PC=memory[PC];
           break; 

        case mul:
           r1=memory[PC];
           PC++;
           result=registers[0]*registers[r1];
           registers[5]=result>>8 & 0xFF;
           registers[0]=result & 0xFF;
           break;



        case stop:
           running=0;
           printf("RUNNED SUCCESFULLY\n");
           break;


        default:
          printf("BUG HAPPENED\n");
          running=0;
          break;
}
       
    }
    
    printf("MUL=%d\n",result);
    printf("R0=%d",registers[0]);
    return 0;
}