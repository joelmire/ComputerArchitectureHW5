#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int log2(int n);

int main(int argc, char *argv[]) {
	// read in address_bits and page_size
	FILE *fp;
	fp = fopen(argv[1], "r");

	int address_bits;
	int page_size;
	fscanf(fp, "%d\t%d", &address_bits, &page_size);
    
    // calculate # of page offset bits
    int pofs_size = log2(page_size);

    // convert the hex virtual address to decimal virtual address
	char va_hex[64];
	strcpy(va_hex, argv[2]);
	int len = strlen(va_hex);
	int va_dec = 0;
	int i = 1;
	while (len > 0) {
		if (va_hex[len - 1] <= '9') 
			va_dec += i * (va_hex[len - 1] - 48);
		else 
			va_dec += i * (va_hex[len - 1] - 87);
		i = i * 16;
		len--;
	}

	// determine pofs
    int pofs;
    pofs = va_dec & ((1 << pofs_size) - 1);

    // determine vpn from va
    int vpn;
    vpn = va_dec >> pofs_size;


    // determine # of virtual pages (should be equivalent to # of ppns in file)
	int num_virtual_pages;
	num_virtual_pages = (2 << address_bits) / (page_size);

    fscanf(fp,"/n/n");

    int k = 0;
    int ppn;
    int pa;
	while (k < num_virtual_pages) {
	  	fscanf(fp, "%d\n", &ppn);
	  	if (k == vpn && ppn == -1) {
	  		printf("PAGEFAULT\n");
	  		return EXIT_SUCCESS;
	  	}
	  	else if (k == vpn && ppn != -1) {
	  		pa = (ppn << pofs_size) | pofs;
	  		break;
	  	}
	 	k++;
	  	num_virtual_pages--;
	}
	printf("%x\n", pa);
	return EXIT_SUCCESS;
}

int log2(int n) { 
    	int r = 0;
    	while (n >>= 1) 
    		r++;
    	return r;
    }