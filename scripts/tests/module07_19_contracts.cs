using System.Reflection;
using System.Runtime.ExceptionServices;
using RouteEngine;
internal static class Contracts
{
 static void Check(bool ok,string why){if(!ok)throw new InvalidOperationException(why);}
 static void Throws<T>(Action action) where T:Exception {try{action();}catch(T){return;}throw new InvalidOperationException("Expected "+typeof(T).Name);}
 static T Call<T>(string name,params object?[] args){try{return (T)typeof(Program).GetMethod(name,BindingFlags.NonPublic|BindingFlags.Static)!.Invoke(null,args)!;}catch(TargetInvocationException ex) when(ex.InnerException!=null){ExceptionDispatchInfo.Capture(ex.InnerException).Throw();throw;}}
 static void Main(){
var graph=new WeightedGraph();graph.AddUndirectedRoad(" A ","B",int.MaxValue);graph.AddUndirectedRoad("B","C",int.MaxValue);graph.AddLocation("Z");var finder=new RouteFinder(graph);var result=finder.FindCheapest(" A "," C ");Check(result.Found && result.TotalCost==2L*int.MaxValue && result.Path.SequenceEqual(new[]{"A","B","C"}),"trimmed endpoints and wide cost");Check(finder.FindCheapest("A","A").TotalCost==0 && !finder.FindCheapest("A","Z").Found,"identity/unreachable");Throws<ArgumentOutOfRangeException>(()=>graph.AddUndirectedRoad("A","Z",0));Throws<KeyNotFoundException>(()=>finder.FindCheapest("missing","C"));Throws<NotSupportedException>(()=>((IList<Road>)graph.GetRoads("A")).Clear());Throws<NotSupportedException>(()=>((IList<string>)result.Path).Clear());
var rng=new Random(719);for(int trial=0;trial<20;trial++){var g=new WeightedGraph();const int n=6;var d=new long[n,n];for(int i=0;i<n;i++){g.AddLocation(i.ToString());for(int j=0;j<n;j++)d[i,j]=i==j?0:1000000;}for(int i=0;i<n;i++)for(int j=i+1;j<n;j++)if(rng.Next(3)==0){int w=rng.Next(1,30);g.AddUndirectedRoad(i.ToString(),j.ToString(),w);d[i,j]=d[j,i]=w;}for(int k=0;k<n;k++)for(int i=0;i<n;i++)for(int j=0;j<n;j++)d[i,j]=Math.Min(d[i,j],d[i,k]+d[k,j]);var f=new RouteFinder(g);for(int i=0;i<n;i++)for(int j=0;j<n;j++){var r=f.FindCheapest(i.ToString(),j.ToString());Check(r.Found==(d[i,j]<1000000),"reachability oracle");if(r.Found){Check(r.TotalCost==d[i,j] && r.Path[0]==i.ToString() && r.Path[^1]==j.ToString(),"route oracle");long cost=0;for(int p=1;p<r.Path.Count;p++)cost+=g.GetRoads(r.Path[p-1]).Single(e=>e.To==r.Path[p]).Cost;Check(cost==r.TotalCost,"reconstructed cost");}}}
 }
}
