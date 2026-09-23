using System.Reflection;
using System.Runtime.ExceptionServices;
using GreedyDemo;
internal static class Contracts
{
 static void Check(bool ok,string why){if(!ok)throw new InvalidOperationException(why);}
 static void Throws<T>(Action action) where T:Exception {try{action();}catch(T){return;}throw new InvalidOperationException("Expected "+typeof(T).Name);}
 static T Call<T>(string name,params object?[] args){try{return (T)typeof(Program).GetMethod(name,BindingFlags.NonPublic|BindingFlags.Static)!.Invoke(null,args)!;}catch(TargetInvocationException ex) when(ex.InnerException!=null){ExceptionDispatchInfo.Capture(ex.InnerException).Throw();throw;}}
 static void Main(){
var rng=new Random(715);for(int trial=0;trial<100;trial++){var a=Enumerable.Range(0,8).Select(i=>{int s=rng.Next(-3,10);return new Session(i.ToString(),s,s+rng.Next(1,5));}).ToArray();int best=0;for(int mask=0;mask<(1<<a.Length);mask++){var subset=a.Where((_,i)=>(mask&(1<<i))!=0).OrderBy(x=>x.Start).ToArray();if(subset.Zip(subset.Skip(1)).All(p=>p.First.End<=p.Second.Start))best=Math.Max(best,subset.Length);}var selected=Call<IReadOnlyList<Session>>("SelectMaximumNonOverlapping",(object)a);Check(selected.Count==best && selected.Zip(selected.Skip(1)).All(p=>p.First.End<=p.Second.Start),"brute force schedule");}Throws<ArgumentException>(()=>Call<object>("SelectMaximumNonOverlapping",(object)new[]{new Session("bad",1,1)}));
 }
}
