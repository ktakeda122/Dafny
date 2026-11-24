{
  // Wrong for the intended behaviour: scans from the END, so it returns the
  // LAST occurrence of key, not the first.
  i := a.Length - 1;
  while i >= 0
    invariant -1 <= i < a.Length
    invariant forall j :: i < j < a.Length ==> a[j] != key
  {
    if a[i] == key { return; }
    i := i - 1;
  }
}
