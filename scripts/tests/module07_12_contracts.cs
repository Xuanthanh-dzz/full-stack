using System.Reflection;
using System.Runtime.ExceptionServices;
using DijkstraDemo;
internal static class Contracts
{
 static void Check(bool ok,string why){if(!ok)throw new InvalidOperationException(why);}
 static void Throws<T>(Action action) where T:Exception {try{action();}catch(T){return;}throw new InvalidOperationException("Expected "+typeof(T).Name);}
 static T Call<T>(string name,params object?[] args){try{return (T)typeof(Program).GetMethod(name,BindingFlags.NonPublic|BindingFlags.Static)!.Invoke(null,args)!;}catch(TargetInvocationException ex) when(ex.InnerException!=null){ExceptionDispatchInfo.Capture(ex.InnerException).Throw();throw;}}
 static void Main(){
var g=(Dictionary<string,Edge[]>)typeof(Program).GetField("Graph",System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Static)!.GetValue(null)!;
var rng=new Random(712);for(int trial=0;trial<20;trial++){g.Clear();const int n=6;var d=new long[n,n];for(int i=0;i<n;i++)for(int j=0;j<n;j++)d[i,j]=i==j?0:1000000;for(int i=0;i<n;i++){var edges=new List<Edge>();for(int j=0;j<n;j++)if(i!=j && rng.Next(3)==0){int w=rng.Next(0,20);edges.Add(new(j.ToString(),w));d[i,j]=w;}g[i.ToString()]=edges.ToArray();}for(int k=0;k<n;k++)for(int i=0;i<n;i++)for(int j=0;j<n;j++)d[i,j]=Math.Min(d[i,j],d[i,k]+d[k,j]);for(int i=0;i<n;i++)for(int j=0;j<n;j++){var r=Call<(long Distance,IReadOnlyList<string> Path)>("ShortestPath",i.ToString(),j.ToString());Check(r.Distance==(d[i,j]>=1000000?long.MaxValue:d[i,j]),"Floyd oracle");if(r.Path.Count>0){Check(r.Path[0]==i.ToString() && r.Path[^1]==j.ToString(),"endpoints");long cost=0;for(int p=1;p<r.Path.Count;p++)cost+=g[r.Path[p-1]].Single(e=>e.To==r.Path[p]).Weight;Check(cost==r.Distance,"path cost");}}}
g.Clear();g["a"]=new[]{new Edge("b",int.MaxValue)};g["b"]=Array.Empty<Edge>();Check(Call<(long,IReadOnlyList<string>)>("ShortestPath","a","b").Item1==int.MaxValue,"valid intMax cost");g["z"]=new[]{new Edge("b",-1)};Throws<ArgumentOutOfRangeException>(()=>Call<object>("ShortestPath","a","a"));g["z"]=new[]{new Edge("unknown",1)};Throws<ArgumentException>(()=>Call<object>("ShortestPath","a","b"));
 }
}
