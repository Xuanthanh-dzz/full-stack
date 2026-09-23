using System.Reflection;
using System.Runtime.ExceptionServices;
using BacktrackingDemo;
internal static class Contracts
{
 static void Check(bool ok,string why){if(!ok)throw new InvalidOperationException(why);}
 static void Throws<T>(Action action) where T:Exception {try{action();}catch(T){return;}throw new InvalidOperationException("Expected "+typeof(T).Name);}
 static T Call<T>(string name,params object?[] args){try{return (T)typeof(Program).GetMethod(name,BindingFlags.NonPublic|BindingFlags.Static)!.Invoke(null,args)!;}catch(TargetInvocationException ex) when(ex.InnerException!=null){ExceptionDispatchInfo.Capture(ex.InnerException).Throw();throw;}}
 static void Main(){
var rng=new Random(716);for(int trial=0;trial<100;trial++){var input=Enumerable.Range(0,8).Select(_=>rng.Next(1,15)).ToArray();var unique=input.Distinct().Order().ToArray();int target=rng.Next(30);var expected=new HashSet<string>();for(int mask=0;mask<(1<<unique.Length);mask++){var subset=unique.Where((_,i)=>(mask&(1<<i))!=0).ToArray();if(subset.Sum()==target)expected.Add(string.Join(",",subset));}var actual=Call<IReadOnlyList<int[]>>("FindCombinations",input,target);Check(actual.Count==expected.Count && expected.SetEquals(actual.Select(x=>string.Join(",",x))),"subset oracle");if(actual.Count>1)Check(!ReferenceEquals(actual[0],actual[1]),"separate snapshots");}var large=Call<IReadOnlyList<int[]>>("FindCombinations",new[]{1,2,int.MaxValue},int.MaxValue);Check(large.Count==1 && large[0].Single()==int.MaxValue,"overflow pruning");Throws<ArgumentException>(()=>Call<object>("FindCombinations",new[]{0,1},1));
 }
}
