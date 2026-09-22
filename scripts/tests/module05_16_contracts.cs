using ExpressionRuleDemo;
using System.Linq.Expressions;
using System.Reflection;
internal static class Contracts
{
    public static void Main()
    {
        var build=typeof(ExpressionRuleDemo.Program).GetMethod("BuildMinimumTotalRule",BindingFlags.Static|BindingFlags.NonPublic)!;
        var tree=(Expression<Func<Order,bool>>)build.Invoke(null,[10m])!;
        var run=tree.Compile();var interpret=tree.Compile(preferInterpretation:true);
        foreach(var total in new[]{9m,10m,11m})
        {var item=new Order("A",total,true);if(run(item)!=(total>=10)||interpret(item)!=run(item))throw new Exception("threshold");}
        var comparison=(BinaryExpression)tree.Body;var member=(MemberExpression)comparison.Left;
        if(!ReferenceEquals(member.Expression,tree.Parameters[0]))throw new Exception("parameter identity");
        decimal live=10m;Expression<Func<Order,bool>> captured=x=>x.Total>=live;var predicate=captured.Compile();live=20m;
        if(predicate(new Order("A",15,true)))throw new Exception("closure was incorrectly snapshot");
    }
}
