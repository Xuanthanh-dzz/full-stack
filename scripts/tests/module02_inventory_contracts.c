#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
/* Inject failures deterministically without exhausting the host's memory. */
static int allocation_number;
static int fail_at;
static void *test_malloc(size_t size)
{
    if (++allocation_number == fail_at) return NULL;
    return malloc(size);
}
static void *test_realloc(void *pointer, size_t size)
{
    if (++allocation_number == fail_at) return NULL;
    return realloc(pointer, size);
}
#define malloc test_malloc
#define realloc test_realloc
#include "inventory.c"
#undef malloc
#undef realloc
#include "storage.h"

int main(void)
{
    for (int failure = 1; failure <= 3; ++failure) {
        Inventory inventory;
        inventory_init(&inventory);
        allocation_number = 0;
        fail_at = failure;
        assert(inventory_add(&inventory, "A", "Alpha", 1, 10) == INV_OUT_OF_MEMORY);
        assert(inventory.count == 0 && inventory_validate(&inventory) == INV_OK);
        inventory_dispose(&inventory);
    }
    fail_at = 0;
    Inventory inventory;
    inventory_init(&inventory);
    for (int index = 0; index < 6; ++index) {
        char code[16];
        int length = snprintf(code, sizeof code, "P%d", index);
        assert(length > 0 && (size_t)length < sizeof code);
        assert(inventory_add(&inventory, code, "Product", 2, 10) == INV_OK);
    }
    assert(inventory.count == 6 && inventory.capacity >= 6);
    assert(inventory_add(&inventory,"P0","Duplicate",1,1)==INV_DUPLICATE);
    assert(inventory_change_quantity(&inventory,"P0",-3)==INV_OUT_OF_RANGE);
    assert(inventory_find(&inventory,"P0")->quantity==2);
    assert(inventory_remove(&inventory,"P2")==INV_OK);
    assert(inventory.count==5 && inventory_find(&inventory,"P2")==NULL);
    assert(inventory_validate(&inventory)==INV_OK);
    assert(storage_save_atomic("roundtrip.txt",&inventory)==INV_OK);
    Inventory loaded;
    inventory_init(&loaded);
    assert(storage_load("roundtrip.txt",&loaded)==INV_OK && loaded.count==5);
    const char *bad[] = {
        "BAD_VERSION\n", "INVENTORY_V1\nA|Alpha|1\n",
        "INVENTORY_V1\nA|Alpha|12x|10\n",
        "INVENTORY_V1\nA|Alpha|1|10\nA|Duplicate|2|10\n",
        "INVENTORY_V1\nA|Alpha|999999999999999999999|10\n",
        "INVENTORY_V1\nA|Alpha|1|10"
    };
    for (size_t index=0; index<sizeof bad/sizeof bad[0]; ++index) {
        FILE *file=fopen("malformed.txt","w");
        assert(file);
        assert(fputs(bad[index],file)>=0);
        assert(fclose(file)==0);
        assert(storage_load("malformed.txt",&loaded)==INV_FORMAT_ERROR);
        assert(loaded.count==5 && inventory_find(&loaded,"P0")->quantity==2);
        assert(inventory_validate(&loaded)==INV_OK);
    }
    assert(remove("roundtrip.txt")==0);
    assert(remove("malformed.txt")==0);
    inventory_dispose(&loaded);
    inventory_dispose(&loaded);
    inventory_dispose(&inventory);
    return 0;
}
