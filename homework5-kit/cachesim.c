#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int log2(int n);
int hextodec(char hex[], int prefix);

int main(int argc, char *argv[]) {
	FILE *fp;
	fp = fopen(argv[1], "r");
	int cache_size = atoi(argv[2]);		// kB
	int ways = atoi(argv[3]);  			
	int block_size = atoi(argv[4]);     // B
	int num_sets = (1 << (10 + log2(cache_size))) / (ways * block_size);		// num_sets = cache size / (ways * block size)

    int cache[num_sets][ways];
    for (int i = 0; i < num_sets; i++) {
    	int j = 0;
    	for (int j = 0; j < ways; j++) {
    		cache[i][j] = -1;
    	}
    }

	unsigned char* memory;
	memory = (unsigned char*)malloc(2 << 24);	  // 16MB memory

	char access_type[64];
	// char address_hex[64];
	int address_dec;
	int access_size;
	int data_dec;
	int tag;

	while (true) {
		
		int content = fgetc(fp);
		if (!(content == 's' || content == 'l')) {
			break;
		}
		ungetc(content, fp);

		fscanf(fp, "%s\t%x\t%d", &access_type[0], &address_dec, &access_size);

		// address_dec = hextodec(address_hex, 1);

		int block_offset_bits;
		int address_bits_wo_block_offset_bits;
		int set_bits;
		int tag_bits;
		int num_block_offset_bits = log2(block_size);

		block_offset_bits = address_dec & ((1 << num_block_offset_bits) - 1);
		address_bits_wo_block_offset_bits = address_dec >> num_block_offset_bits;
        int num_set_bits = log2(num_sets);
		set_bits = address_bits_wo_block_offset_bits & ((1 << num_set_bits) - 1);
		tag_bits = address_bits_wo_block_offset_bits >> num_set_bits;
		int num_tag_bits = 24 - num_set_bits - num_block_offset_bits;

        int hit = 0;	

		if (access_type[0] == 's') {
			int k = 0;
			while (k < access_size) {
				// printf("k is: %d\n", k);
				// printf("access_size is: %d\n", access_size);
		 		// fscanf(fp, "%02hhx", &memory[address_dec + k]); 
		 		fscanf(fp, "%02hhx", &memory[address_dec + k]); 
				k++;
			}
			fscanf(fp, "\n");

			int i = 0;
		    while (i < ways) {
		    	int m = i;
		    	if (tag_bits == cache[set_bits][i]) {
		    		hit = 1;	    			
		    		while (m > 0) {
		    		    cache[set_bits][m] = cache[set_bits][m - 1];
		    			m--;
		    	    }
		    		cache[set_bits][0] = tag_bits;
		    		break;
		    	}
		    	i++;
		    }

		    if (hit == 1)
		   		printf("%s 0x%x hit\n", access_type, address_dec);
		    if (hit == 0) 
		    	printf("%s 0x%x miss\n", access_type, address_dec);
		}

		if (access_type[0] == 'l') {

			int i = 0;
		    while (i < ways) {
		    	int m = i;
		    	if (tag_bits == cache[set_bits][i]) {
		    		hit = 1;	    			
		    		while (m > 0) {
		    		    cache[set_bits][m] = cache[set_bits][m - 1];
		    			m--;
		    	    }
		    		cache[set_bits][0] = tag_bits;
		    		break;
		    	}
		    	i++;
		    }

			if (hit == 1) {
				printf("%s 0x%x hit ", access_type, address_dec);
				int j = 0;
				while (j < access_size) {
	 	    		printf("%02hhx", memory[address_dec + j]);
	 	    		j++;
	 	    	}
	 	    	printf("\n");
			}

			if (hit == 0) {
				printf("%s 0x%x miss ", access_type, address_dec);
				int j = 0;
				while (j < access_size) {
	 	    		printf("%02hhx", memory[address_dec + j]);
	 	    		j++;
	 	    	}
	 	    	printf("\n");

	 	    	int i = ways - 1;
	 	        while (i > 0) {
	 	        	cache[set_bits][i] = cache[set_bits][i - 1];
	 	        	i--;
	 	        }
	 	        cache[set_bits][0] = tag_bits; 
			}	
			fscanf(fp, "\n"); 
		}
	}
	free(memory);
	return EXIT_SUCCESS;

}


int log2(int n) { 
	int r = 0;
    while (n >>= 1) {
    	r++;
    }
    return r; 
}

// int hextodec(char hex[], int prefix) {
// 	int dec;
// 	int length = strlen(hex);
// 	int i = 1;
// 	int base_val;
// 	if (prefix == 1)
// 		base_val = 2;
// 	else
// 		base_val = 0;
// 	while (length > base_val) {
// 		if (hex[length - 1] <= '9')
// 		    dec += i * (hex[length - 1] - 48);
// 		else 
// 		    dec += i * (hex[length - 1] - 87);
// 		i = i * 16;
// 		length--;
// 	}
//     return dec;
// }