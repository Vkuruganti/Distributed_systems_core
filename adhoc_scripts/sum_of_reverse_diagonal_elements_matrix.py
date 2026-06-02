# Author: Vas Kuruganti
# function to return the sum of reverse diagonal elements in a matrix
def reverse_d(a):
      m = []
      k = [(i,j) for i in range(3) for j in reversed(range(3))]
      m.append(k[0])
      m.append(k[int((len(k)-1)/2)])
      m.append(k[-1])
      p = [a[i][j] for i,j in m]
      return(sum(p))
