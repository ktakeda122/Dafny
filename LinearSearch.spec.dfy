// HW 8-2: linear search. Signature, requires and ensures only; the body is missing on purpose.
// Intended behaviour (like Python's list.index, but returning -1): the index of the
// FIRST occurrence of key in a, or -1 if key does not occur.
method LinearSearch(a: array<int>, key: int) returns (i: int)
  ensures 0 <= i ==> i < a.Length && a[i] == key
  ensures i < 0 ==> forall j :: 0 <= j < a.Length ==> a[j] != key
