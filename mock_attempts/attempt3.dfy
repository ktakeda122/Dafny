{
  i := 0;
  while i < a.Length
    invariant 0 <= i <= a.Length
    invariant forall j :: 0 <= j < i ==> a[j] != key
  {
    if a[i] == key { return; }
    i := i + 1;
  }
  i := -1;
}
