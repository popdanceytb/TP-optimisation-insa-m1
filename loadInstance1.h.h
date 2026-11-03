int loadInstance(char* instances, int option)
{
    char aux[50];
    ifstream file(instances);
    if (file==NULL)
    {
      cout << "Error opening data file.";
      return(1);
    }
    
    file >> n >> m >> comps >> K >> H ;    //stations products compartments vehicles periods
    s = comps; 
    
    int **distTemp;
    
    dist = new int*[n+1];
    distTemp = new int*[n+1];
    for (int i=0; i < n+1; i++)
    { 
      dist[i] = new int [n+1];  
      distTemp[i] = new int[n+1];
    }
    
    TPoint *CoorTemp;
    
    Coor = new TPoint [n+1];
    CoorTemp = new TPoint [n+1];
    
    file >> CoorTemp[0].X >> CoorTemp[0].Y;
    
    comp = new int*[K+1];
    for (int i=1; i<K+1; ++i)
    {
        comp[i] = new int[comps+1];
    	for (int j=1; j<comps+1; ++j)
    		file >> comp[i][j];
    }
    
    int ***rTemp;
    
    r = new int**[n+2];
    rTemp = new int**[n+2];
    for (int i=0; i < n+2; i++)
    {
      r[i] = new int* [m+1];
      rTemp[i] = new int*[m+1];
      for (int l=1; l<m+1; ++l)
      {
		r[i][l] = new int [H+2];
		rTemp[i][l] = new int [H+2];
	  }
    }
    
    int **UTemp, **I0Temp;
    double **hTemp;
    U  = new int* [n+2];
    UTemp = new int*[n+2];
    h  = new double* [n+2];
    hTemp = new double*[n+2];
    I0 = new int* [n+2];
    I0Temp = new int*[n+2];
    for (int i=1; i<n+1; ++i)
    {
      U[i]  = new int [m+1]; 
      UTemp[i] = new int [m+1];
      h[i]  = new double [m+1];
      hTemp[i] = new double [m+1];
      I0[i] = new int [m+1];
      I0Temp[i] = new int [m+1];
    }
    
    
    for (int i=1; i < n+1; i++)
    {
      file >> CoorTemp[i].X >> CoorTemp[i].Y ;
      for (int l=1; l<m+1; ++l)
      {
	      file >> I0Temp[i][l] ;
      }
      
      for (int l=1; l<m+1; ++l)
      {
			for (int t=1; t<H+1; ++t)
			{
			  file >> rTemp[i][l][t] ;
			}
			r[i][l][0] = 0;
			r[i][l][H+1] = 0;
      }
      for (int l=1; l<m+1; ++l)
      {
      	file >> UTemp[i][l] >> aux;
      	hTemp[i][l] = atof(aux);
      }
    }
    

    for (int i = 0; i < n+1; i++)
      for (int j = 0; j < n+1; j++)
		distTemp[i][j] = (int)floor(sqrt((double)((CoorTemp[i].X - CoorTemp[j].X)*(CoorTemp[i].X - CoorTemp[j].X) + (CoorTemp[i].Y - CoorTemp[j].Y)*(CoorTemp[i].Y - CoorTemp[j].Y))) + 0.5);



//select criterion to order the input:

if (option == 0) //random
{
	for (int i=1; i<n+1; ++i)
	{
		for (int j=0; j<n+1; ++j)
			dist[i][j] = distTemp[i][j];
	}
	for (int i=1; i<n+1; ++i)
		for (int l=1; l<m+1; ++l)
		{
			I0[i][l] = I0Temp[i][l];
			U[i][l] = UTemp[i][l];
			h[i][l] = hTemp[i][l];
			for (int t=1; t<H+1; ++t)
				r[i][l][t] = rTemp[i][l][t];
		}
	
}
else if (option == 1) //total demand
{
   int totalDemand[n+1];
   int sequence[n+1];
   sequence[0]=0;
   for (int i=1; i<n+1; ++i)
   {
   	  totalDemand[i] = 0;
      for (int l=1; l<m+1; ++l)
        for (int t=1; t<H+1; ++t)
        	totalDemand[i] += rTemp[i][l][t];
      sequence[i] = i;
   }
     
   int aux=0; 
   for (int i=1; i<n+1; ++i)
     for (int j=i+1; j<n+1; ++j)
     {
     	if (totalDemand[i] < totalDemand[j])
     	{
     		aux = totalDemand[j];
     		totalDemand[j] = totalDemand[i];
     		totalDemand[i] = aux;
     		aux = sequence[i];
     		sequence[i] = sequence[j];
     		sequence[j] = aux;
     	}
     }
     
    //the new sequence of customers is store in sequence[]

	for (int i=0; i<n+1; ++i)
	{
		for (int j=0; j<n+1; ++j)
			dist[i][j] = distTemp[sequence[i]][sequence[j]];
	}
	for (int i=1; i<n+1; ++i)	
		for (int l=1; l<m+1; ++l)
		{
			I0[i][l] = I0Temp[sequence[i]][l];
			U[i][l] = UTemp[sequence[i]][l];
			h[i][l] = hTemp[sequence[i]][l];
			for (int t=1; t<H+1; ++t)
				r[i][l][t] = rTemp[sequence[i]][l][t];
		}
	




}
else if (option == 2) //demand for product 1
{
   int totalDemand[n+1];
   int sequence[n+1];
   sequence[0]=0;
   for (int i=1; i<n+1; ++i)
   {
   	  totalDemand[i] = 0;
      for (int t=1; t<H+1; ++t)
        totalDemand[i] += rTemp[i][1][t];
      sequence[i] = i;
   }
     
   int aux=0; 
   for (int i=1; i<n+1; ++i)
     for (int j=i+1; j<n+1; ++j)
     {
     	if (totalDemand[i] < totalDemand[j])
     	{
     		aux = totalDemand[j];
     		totalDemand[j] = totalDemand[i];
     		totalDemand[i] = aux;
     		aux = sequence[i];
     		sequence[i] = sequence[j];
     		sequence[j] = aux;
     	}
     }
     
    //the new sequence of customers is store in sequence[]

	for (int i=0; i<n+1; ++i)
	{
		for (int j=0; j<n+1; ++j)
			dist[i][j] = distTemp[sequence[i]][sequence[j]];
	}
	for (int i=1; i<n+1; ++i)	
		for (int l=1; l<m+1; ++l)
		{
			I0[i][l] = I0Temp[sequence[i]][l];
			U[i][l] = UTemp[sequence[i]][l];
			h[i][l] = hTemp[sequence[i]][l];
			for (int t=1; t<H+1; ++t)
				r[i][l][t] = rTemp[sequence[i]][l][t];
		}
	



}
else if (option == 3) //proximity to the supplier
{
   int distance[n+1];
   int sequence[n+1];
   sequence[0]=0;
   for (int i=1; i<n+1; ++i)
   {
      distance[i] = distTemp[0][i];
      sequence[i] = i;
   }
     
   int aux=0; 
   for (int i=1; i<n+1; ++i)
     for (int j=i+1; j<n+1; ++j)
     {
     	if (distance[i] > distance[j])
     	{
     		aux = distance[j];
     		distance[j] = distance[i];
     		distance[i] = aux;
     		aux = sequence[i];
     		sequence[i] = sequence[j];
     		sequence[j] = aux;
     	}
     }
     
    //the new sequence of customers is store in sequence[]

	for (int i=0; i<n+1; ++i)
	{
		for (int j=0; j<n+1; ++j)
			dist[i][j] = distTemp[sequence[i]][sequence[j]];
	}
	for (int i=1; i<n+1; ++i)	
		for (int l=1; l<m+1; ++l)
		{
			I0[i][l] = I0Temp[sequence[i]][l];
			U[i][l] = UTemp[sequence[i]][l];
			h[i][l] = hTemp[sequence[i]][l];
			for (int t=1; t<H+1; ++t)
				r[i][l][t] = rTemp[sequence[i]][l][t];
		}

}
else if (option == 4) //proximity to the supplier
{
   int distance[n+1];
   int sequence[n+1];
   sequence[0]=0;
   for (int i=1; i<n+1; ++i)
   {
      distance[i] = distTemp[0][i];
      sequence[i] = i;
   }
     
   int aux=0; 
   for (int i=1; i<n+1; ++i)
     for (int j=i+1; j<n+1; ++j)
     {
     	if (distance[i] < distance[j])
     	{
     		aux = distance[j];
     		distance[j] = distance[i];
     		distance[i] = aux;
     		aux = sequence[i];
     		sequence[i] = sequence[j];
     		sequence[j] = aux;
     	}
     }
     
    //the new sequence of customers is store in sequence[]

	for (int i=0; i<n+1; ++i)
	{
		for (int j=0; j<n+1; ++j)
			dist[i][j] = distTemp[sequence[i]][sequence[j]];
	}
	for (int i=1; i<n+1; ++i)	
		for (int l=1; l<m+1; ++l)
		{
			I0[i][l] = I0Temp[sequence[i]][l];
			U[i][l] = UTemp[sequence[i]][l];
			h[i][l] = hTemp[sequence[i]][l];
			for (int t=1; t<H+1; ++t)
				r[i][l][t] = rTemp[sequence[i]][l][t];
		}

}
			
	

    return 0;
}