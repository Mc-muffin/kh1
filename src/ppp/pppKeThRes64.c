#include "ppp.h"

void pppKeThRes64Con(pppPObject* pobj, pppCtrlTable* ctbl) {
    KeThResHd_Init(&pobj->val[ctbl->useVal[0]], 1, 64);
}
