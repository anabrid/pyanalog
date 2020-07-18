//#define RK
//#define TRAPEZ

#ifdef TRAPEZ
void __integrate(double *i, double y, double dx, double *y_old)
{
  *i -= (y + *y_old) / 2. * dx;
  *y_old = y;
}
#elif defined RK
#else // Euler
void __integrate(double *i, double y, double dx, double *y_old)
{
  *i -= y * dx;
}
#endif
